import qdrant_client
import threading

from langchain.schema import Document
from langchain_community.document_loaders import UnstructuredAPIFileLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.qdrant import Qdrant
from langchain.chains.llm import LLMChain
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain.chat_models.base import BaseChatModel

from . import prompt
from .database import PromptHandler, ResponseStorer
from pydantic import BaseModel, Field, field_validator


class KnowledgeManager:
    def __init__(
        self,
        prompt_handler: PromptHandler,
        response_handler: ResponseStorer,
        openai_api_key: str,
        qdrant_url: str,
        qdrant_api_key: str,
        unstructured_api_key: str,
        llm: BaseChatModel,
        insights_index_name: str = "INSIGHTS_INDEX",
        unstructured_api_url: str = None,
        docs_limit: int = 3500,
        chunk_size=2000,
        collection_name: str = "books",
    ) -> None:
        self.openai_api_key = openai_api_key
        self.qdrant_url = qdrant_url
        self.qdrant_api_key = qdrant_api_key
        self.docs_limit = docs_limit
        self.unstructured_api_url = unstructured_api_url
        self.response_handler = response_handler
        self.prompt_handler = prompt_handler
        self.INSIGHTS_INDEX = insights_index_name
        self.chunk_size = chunk_size
        self.unstructured_api_key = unstructured_api_key
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
        
    def injest_data_api(
        self, text: str = "", file_path: str = "", collection_name: str = None
    ) -> list[str]: 
        if not collection_name:
            collection_name = self.collection_name
            
        print(f"Injesting data to collection: {collection_name}")
        if not text and not file_path:
            raise ValueError("No data provided")

        if text:
            docs = [Document(page_content=text, metadata={"source": "injest"})]
            docs = CharacterTextSplitter(
                chunk_size=self.chunk_size
            ).split_documents(docs)
            print("Text split")
        else:
            loader = UnstructuredAPIFileLoader(
                file_path=file_path,
                api_key=self.unstructured_api_key,
                url=self.unstructured_api_url
            )
            docs = loader.load()
            splitter = CharacterTextSplitter(chunk_size=self.chunk_size)
            docs = splitter.split_documents(docs)
            print("FIle split")


        embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        print("Embedding data")
        qdrant: Qdrant = Qdrant.construct_instance(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
            texts=["test"],
            embedding=embeddings,
            collection_name=collection_name,
            timeout=50,
            prefer_grpc=True
        )
        print("Already exists")
        return qdrant.add_documents(docs), "\n".join([doc.page_content for doc in docs])

    def load_vectorstore(self, collection_name: str) -> Qdrant:
        client = qdrant_client.QdrantClient(
            url=self.qdrant_url, api_key=self.qdrant_api_key
        )
        return Qdrant(
            client=client,
            collection_name=collection_name,
            embeddings=OpenAIEmbeddings(openai_api_key=self.openai_api_key),
        )

    def _reduce_tokens_below_limit(self, docs: list, docs_token_limit: int):
        num_docs = len(docs)
        tokens = [len(doc.page_content) for doc in docs]
        token_count = sum(tokens[:num_docs])
        while token_count > docs_token_limit:
            num_docs -= 1
            token_count -= tokens[num_docs]
        return docs[:num_docs]

    def chat(
        self,
        question: str,
        chat_history: list[tuple[str, str]],
        collection_name: str = None,
        wait_for_insights: bool = False,
        get_highest_ranking_response: bool = False,
        company: str = None,
        department: str = None,
        role: str = None,
        prefix: str = None
    ) -> str:
        if get_highest_ranking_response:
            if resp := self.response_handler.get_highest_rank_response(question):
                return resp.response
        
        if not collection_name:
            collection_name = self.collection_name

        try:
            vectorstore = self.load_vectorstore(collection_name)
            documents = vectorstore.similarity_search(question, k=6)
            documents = self._reduce_tokens_below_limit(documents, self.docs_limit)
        except Exception:
            documents = []
            
        try:
            insights = self.docs_to_string(
                self._reduce_tokens_below_limit(
                    self.load_vectorstore(self.INSIGHTS_INDEX).similarity_search(
                        question, k=2
                    ),
                    6000,
                )
            )
        except Exception as e:
            insights = ""


        chain = LLMChain(
            prompt=self.get_prompt(company=company or "unknown", department=department or "unknown", company_role=role or"unknown", prefix=prefix),
            llm=self.llm,
            verbose=True,
        )
        chat_history = self.format_messages(chat_history, 800, "Teacher")
        result = chain.run(
            insights=insights,
            human_question=question,
            data=self.docs_to_string(documents),
            chat_history=chat_history,
            role="Teacher",
            job="Teach students about sales, based on the data given",
        )
        t = threading.Thread(target=self.store_insights, args={question, result})
        t.start()
        if wait_for_insights:
            t.join()

        self.response_handler.create_new_response(question, result)
        return result
    
    def store_insights(self, question: str, response: str):
        chain = LLMChain(
            prompt=prompt.INSIGHT_PROMPT,
            llm=ChatOpenAI(
                openai_api_key=self.openai_api_key,
                temperature=0,
                model="gpt-3.5-turbo-16k",
            ),
            verbose=True,
        )
        insights = chain.run(question=question, answer=response)
        insights = f"\nQuestion: {question}\n Previous Answer: {response} \n Improvements: {insights}"
        self.injest_data_api(text=insights, collection_name=self.INSIGHTS_INDEX)

    def docs_to_string(self, docs):
        return "\n\n".join(
            [self.format_document(doc, prompt.EXAMPLE_PROMPT) for doc in docs]
        )

    def format_document(self, doc: Document, question: PromptTemplate) -> str:
        """Format a document into a string based on a question template."""
        base_info = {"page_content": doc.page_content}
        base_info |= doc.metadata
        if missing_metadata := set(question.input_variables).difference(base_info):
            required_metadata = [
                iv for iv in question.input_variables if iv != "page_content"
            ]
            raise ValueError(
                f"Document question requires documents to have metadata variables: "
                f"{required_metadata}. Received document with missing metadata: "
                f"{list(missing_metadata)}."
            )
        document_info = {k: base_info[k] for k in question.input_variables}
        return question.format(**document_info)

    def format_messages(
        self, chat_history: list[tuple[str, str]], tokens_limit: int, role: str
    ) -> str:
        chat_history = [
            (f"Human: {history[0]}", f"{role}: {history[1]}")
            for history in chat_history
        ]
        tokens_used = 0
        cleaned_msgs = []
        for history in reversed(chat_history):
            tokens_used += len(history[0]) + len(history[1])
            if tokens_used > tokens_limit:
                break
            else:
                cleaned_msgs.append((history[0], history[1]))

        return "\n\n".join(
            reversed(
                [clean_msg[0] + "\n\n" + clean_msg[1] for clean_msg in cleaned_msgs]
            )
        )

    def collection_exists(self, collection: str) -> bool:
        try:
            client = qdrant_client.QdrantClient(
                url=self.qdrant_url, api_key=self.qdrant_api_key, prefer_grpc=True
            )
            client.get_collection(collection)
            return True
        except Exception:
            return False

    def delete_collection(self, collection_name: str) -> bool:
        qdrant = qdrant_client.QdrantClient(
            url=self.qdrant_url,
            prefer_grpc=True,
            api_key=self.qdrant_api_key,
        )
        return qdrant.delete_collection(collection_name)

    def delete_ids(self, ids: list[str]) -> bool:
        client = qdrant_client.QdrantClient(
            url=self.qdrant_url,
            prefer_grpc=True,
            api_key=self.qdrant_api_key,
        )
        qdrant = Qdrant(
            client=client,
            collection_name=self.collection_name,
            embeddings=OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        )
        return qdrant.delete(ids)

    def get_prompt(self, company: str, department: str, company_role: str, prefix: str):
        try:
            return PromptTemplate(
                template=self.prompt_handler.get_main_prompt().content,
                input_variables=self.prompt_variables,
                partial_variables={"company" : company or "", "department" : department or "", "company_role" : company_role or "", "prompt_prefix" : prefix or ""}
            )
        except Exception as e:
            print("Problem in getting main question.", e)
            return PromptTemplate(
                template=prompt.DEFAULT_PROMPT,
                input_variables=self.prompt_variables,
                partial_variables={"company" : company or "", "department" : department or "", "company_role" : company_role or "", "prompt_prefix" : prefix or ""}
            )

    def add_prompt(self, prompt: str, name: str, is_main: bool) -> bool:
        try:
            if is_main:
                try:
                    self.prompt_handler.get_main_prompt()
                    print("Main already exists")
                    return False
                except Exception:
                    ...
            PromptTemplate(template=prompt, input_variables=self.prompt_variables)
            self.prompt_handler.create_prompt(name, is_main, prompt)
        except Exception as e:
            raise ValueError("""Prompt must have placeholders like {{}} for self.prompt_variables
            "insights",
            "human_question",
            "data",
            "chat_history",
            "role",
            "job",
        """)
            return False

    def choose_main_prompt(self, name: str) -> bool:
        try:
            self.prompt_handler.choose_main_prompt(name)
            return True
        except Exception:
            return False


class Scenario(BaseModel):
    name: str = Field(..., json_schema_extra={"description": "A name for the scenario", "example": "Scenario 1"})
    description: str = Field(..., json_schema_extra={"description": "Short description for the scenario"})
    scenario: str = Field(
        ...,
        json_schema_extra={
            "description": "The scenario, You may include what the customer says (Last parts of the conversation or what they last said) but make it clear. Be detailed",
        },
    )
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
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key

    def generate_scenario(self, theme: str) -> Scenario:
        parser = PydanticOutputParser(pydantic_object=Scenario)
        gen_prompt = PromptTemplate(
            template=prompt.SCENARIO_GEN_PROMPT,
            input_variables=["theme"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        llm = ChatOpenAI(
            temperature=0.2,
            openai_api_key=self.openai_api_key,
            model="gpt-3.5-turbo-16k",
        )
        chain = LLMChain(llm=llm, prompt=gen_prompt, verbose=True, output_parser=parser, llm_kwargs={"response_format": {"type": "json_object"}})
        return chain.run(theme=theme)


    def evaluate_scenario(
        self,
        scenario: str,
        best_response: str,
        explanation: str,
        salesman_response: str,
    ) -> ScenarioEvaluationResult:
        llm = ChatOpenAI(
            temperature=0.2,
            openai_api_key=self.openai_api_key,
            model="gpt-3.5-turbo-16k",
        )
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
        chain = LLMChain(llm=llm, prompt=eval_prompt, verbose=True, output_parser=parser, llm_kwargs={"response_format": {"type": "json_object"}})
        return chain.run(
            scenario=scenario,
            best_response=best_response,
            explanation=explanation,
            salesman_response=salesman_response,
        )

