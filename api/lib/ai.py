from typing import Dict, List, Optional, Tuple, Union
from langchain.schema import Document, BaseMessage, AIMessage, HumanMessage, LLMResult
from langchain_community.document_loaders.unstructured import UnstructuredFileLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.llm import LLMChain
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain.chat_models.base import BaseChatModel
from langchain.callbacks.base import BaseCallbackHandler
from langchain_google_firestore import FirestoreVectorStore
from langchain_core.document_loaders.base import BaseLoader
from firebase_admin import credentials, firestore, initialize_app
from google.cloud.firestore_v1.vector import Vector  # type: ignore
from extractous import Extractor, TesseractOcrConfig, PdfOcrStrategy, PdfParserConfig
from pydantic import BaseModel, Field, field_validator
from . import prompt

import firebase_admin
import time




def split_into_chunks(text, chunk_size):
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

class CustomCallback(BaseCallbackHandler):
    def __init__(self, callback, on_end_callback) -> None:
        self.callback = callback
        self.on_end_callback = on_end_callback
        super().__init__()
        self.cached = True

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if token:
            self.cached = False
        if not self.cached:
            self.callback(token)

    def on_llm_end(self, response: LLMResult, *args, **kwargs) -> None:
        if self.cached:
            for chunk in split_into_chunks(response.generations[0][0].text, 8):
                self.callback(chunk)
                time.sleep(0.05)
        self.callback(None)
        self.on_end_callback(response.generations[0][0].text)
     
class FirestoreVectorStoreModified(FirestoreVectorStore):
    def _similarity_search(
        self,
        query: list[float],
        k: int = 10,  # Assuming DEFAULT_TOP_K is 10
        filters: dict = None,
    ) -> list:
        _filters = filters or self.filters
        query_ref = self.collection  # Start with the collection

        if _filters is not None:
            for field, operation, value in _filters:
                query_ref = query_ref.where(field, operation, value)

        results = query_ref.find_nearest(
            vector_field=self.embedding_field,
            query_vector=Vector(query),
            distance_measure=self.distance_strategy,
            limit=k,
        )

        return results.get()  

class ExtractousLoader(BaseLoader):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def load(self):
        pdf_config = PdfParserConfig().set_ocr_strategy(PdfOcrStrategy.NO_OCR)
        extractor = Extractor().set_ocr_config(TesseractOcrConfig().set_language("eng")).set_pdf_config(pdf_config)
        data = extractor.extract_file_to_string(self.file_path)
        return [Document(
            page_content=data[0]
        )]
    

class KnowledgeManager:
    def __init__(
        self,
        openai_api_key: str,
        llm: BaseChatModel,
        docs_limit: int = 3500,
        chunk_size: int = 7000,
        collection_name: str = "books",
    ) -> None:
        self.openai_api_key = openai_api_key
        self.docs_limit = docs_limit
        self.chunk_size = chunk_size
        self.collection_name = collection_name
        self.prompt_variables = [
            "insights",
            "human_question",
            "data",
            "chat_history",
            "role",
            "job",
        ]
        self.llm = llm
        self.vectorstore = self.load_vectorstore(collection_name)
       
    @staticmethod
    def create_filters(criteria: Dict[str, Union[str, List[str]]]) -> List[Tuple[str, str, Union[str, List[str]]]]:
        filters = []
        for key, value in criteria.items():
            if isinstance(value, list):
                filters.append((f'metadata.{key}', 'in', value))
            else:
                filters.append((f'metadata.{key}', '==', value))
        return filters
    
    def ingest_data_api(
        self,
        role: str,
        text: Optional[str] = None,
        file_path: Optional[str] = None,
        collection_name: Optional[str] = None,
        weight: int = 1,
    ) -> tuple[list[str], str]: 
        "Ingests data into the vectorstore, Returns vectorids and the content of file."
        
        if not collection_name:
            collection_name = self.collection_name
            
        if not text and not file_path:
            raise ValueError("No data provided")

        metadata = {"weight": weight}
        if role:
            metadata["role"] = role

        if text:
            docs = [Document(page_content=text, metadata=metadata)]
        else:
            try:
                loader = ExtractousLoader(file_path=file_path)
                docs = [Document(page_content=doc.page_content, metadata=metadata) for doc in loader.load()]
            except Exception:
                loader = UnstructuredFileLoader(file_path=file_path, strategy="fast")
                docs = [Document(page_content=doc.page_content, metadata=metadata) for doc in loader.load()]
            
            splitter = CharacterTextSplitter(chunk_size=self.chunk_size)
            docs = splitter.split_documents(docs)

        embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        vectorstore = FirestoreVectorStoreModified(collection_name, embeddings)

        return vectorstore.add_documents(docs), "\n".join([doc.page_content for doc in docs])

    def load_vectorstore(self, collection_name: str) -> FirestoreVectorStoreModified:
        return FirestoreVectorStoreModified(
            collection_name, 
            OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        )

    def _reduce_tokens_below_limit(self, docs: list[Document], docs_token_limit: int):
        docs = sorted(docs, key=lambda doc: doc.metadata.get('weight', 1), reverse=True)
        num_docs = len(docs)
        tokens = [len(doc.page_content) for doc in docs]
        token_count = sum(tokens[:num_docs])

        while token_count > docs_token_limit:
            num_docs -= 1
            token_count -= tokens[num_docs]

        return docs[:num_docs] 
    
    def chat_stream(
        self,
        question: str,
        chat_history: list[tuple[str, str]],
        role: str,
        prefix: str,
        llm: BaseModel = None
    ) -> str:
        if not llm:
            llm = self.llm

        start_vectorstore = time.time()
        try:
            documents = self.vectorstore.similarity_search(question, k=3, filter=self.create_filters({"role" : [role, "all"]}))
            if not documents:
                print(f"Documents not found for role {role}. Defaulting to all data")
                documents = self.vectorstore.similarity_search(question, k=3)
            documents = self._reduce_tokens_below_limit(documents, self.docs_limit)
        except Exception as e:
            documents = []

        print(f"Time taken for data loading: {time.time() - start_vectorstore}")

        prompt = self.get_prompt()
        document_chain = create_stuff_documents_chain(llm, prompt)
        messages = self.format_messages(chat_history)
        return document_chain.invoke(
            {
                "context": documents,
                "prompt_prefix" : prefix,
                "company_role" : role,
                "messages": [
                    *messages,
                    HumanMessage(content=question)
                ],
            },
            config={"verbose" : True}
        )

    def format_messages(
        self,
        chat_history: List[Tuple[str, str]],
    ) -> List[BaseMessage]:
        messages: List[BaseMessage] = []
        for human_msg, ai_msg in chat_history:
            messages.append(HumanMessage(content=human_msg))
            messages.append(AIMessage(content=ai_msg))
        return messages

    def get_file_metadata(self, id: str):
        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate()
            initialize_app(cred)

        # Get Firestore client
        db = firestore.client()

        # Query Firestore collection and get document by id
        doc_ref = db.collection(self.collection_name).document(id)
        doc = doc_ref.get()

        if doc.exists:
            # Access metadata field
            metadata = doc.to_dict().get('metadata', {})
            return metadata
        else:
            return None
            
    def update_metadata(self, ids: List[str], update_dict: Dict[str, str], collection_name: Optional[str] = None):
        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate()
            initialize_app(cred)

        # Get Firestore client
        db = firestore.client()

        # Use the provided collection name or default to self.collection_name
        collection_name = collection_name or self.collection_name

        # Create a batch to perform multiple updates
        batch = db.batch()

        for id in ids:
            # Get reference to the document
            doc_ref = db.collection(collection_name).document(id)

            # Prepare the update operation
            update_operation = {
                f"metadata.{key}": value for key, value in update_dict.items()
            }

            # Add update operation to the batch
            batch.update(doc_ref, update_operation)

        # Commit the batch
        batch.commit()

        print(f"Updated metadata for {len(ids)} documents in collection {collection_name}")

    def delete_ids(self, ids: list[str]) -> bool:
        vs = self.load_vectorstore(self.collection_name)
        return vs.delete(ids)

    def get_prompt(self):
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    prompt.DEFAULT_PROMPT,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )


class Scenario(BaseModel):
    name: str = Field(..., json_schema_extra={"description": "A name for the scenario", "example": "Scenario 1"})
    description: str = Field(..., json_schema_extra={"description": "Short description for the scenario"})
    best_response: str = Field(..., json_schema_extra={"description": "The solution for the scenario"})
    explanation: str = Field(..., json_schema_extra={"description": "Why the solution was correct"})
    difficulty: str = Field(..., json_schema_extra={"description": "The difficulty of the question from A to C, C being the most difficult"})
    importance: str = Field(..., json_schema_extra={"description": "The importance of the question from 1 to 3. 1 being the most imporant"})

    @field_validator("difficulty")
    def difficulty_range(cls, field):
        if field not in ["A", "B", "C"]:
            raise ValueError("Difficulty must be from A-C")
        return field
    
    @field_validator("importance")
    def importance_range(cls, field):
        if field not in ["1", "2", "3"]:
            raise ValueError("IMportance must be from 1 to 3")
        return field

class ScenarioEvaluationResult(BaseModel):
    grade: str = Field(..., json_schema_extra={"description": "A grade according to the criteria"})
    message: str = Field(..., json_schema_extra={"description": "A message for the salesman on how to improve"})
    best_response: str = Field(..., json_schema_extra={"description": "What could have been a better response"})

class RolePlayingScenarioGenerator:
    def __init__(self, llm):
        self.llm = llm

    def generate_scenario(self, theme: str, data: str, prompt_in: str, llm: BaseModel = None) -> Scenario:
        if not llm:
            llm = self.llm
            
        gen_prompt = PromptTemplate(
            template=prompt.SCENARIO_GEN_PROMPT,
            input_variables=["theme", "data", "prompt"],
        )
        chain = LLMChain(llm=llm, prompt=gen_prompt, verbose=True)
        return chain.run(theme=theme, data=data, prompt=prompt_in)

    def generate_scenario_metadata(self, scenario: str) -> Scenario:
        parser = PydanticOutputParser(pydantic_object=Scenario)
        gen_prompt = PromptTemplate(
            template=prompt.SCENARIO_METADATA_GEN_PROMPT,
            input_variables=["scenario"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        chain = LLMChain(llm=self.llm, prompt=gen_prompt, verbose=True, output_parser=parser, llm_kwargs={"response_format": {"type": "json_object"}})
        return chain.run(scenario=scenario)

    def evaluate_scenario(
        self,
        scenario: str,
        best_response: str,
        explanation: str,
        salesman_response: str,
    ) -> ScenarioEvaluationResult:
        parser = PydanticOutputParser(pydantic_object=ScenarioEvaluationResult)
        eval_prompt = PromptTemplate(
            template=prompt.SCENARIO_EVAL_PROMPT,
            input_variables=[
                "scenario",
                "best_response",
                "explanation",
                "salesman_response",
            ],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        chain = LLMChain(llm=self.llm, prompt=eval_prompt, verbose=True, output_parser=parser, llm_kwargs={"response_format": {"type": "json_object"}})
        return chain.run(
            scenario=scenario,
            best_response=best_response,
            explanation=explanation,
            salesman_response=salesman_response,
        )
