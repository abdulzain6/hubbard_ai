from .lib.database import PromptHandler
from .lib.ai import KnowledgeManager, RolePlayingScenarioGenerator
from .settings import *
from langchain_openai import ChatOpenAI


manager = KnowledgeManager(
    openai_api_key=OPENAI_API_KEY,
    prompt_handler=PromptHandler(),
    qdrant_url=QDRANT_URL,
    qdrant_api_key=QDRANT_API_KEY,
    unstructured_api_url=UNSTRUCTURED_URL,
    unstructured_api_key=UNSTRUCTURED_API_KEY,
    collection_name="books_real_main",
    llm=ChatOpenAI(model=GLOBAL_MODEL, temperature=1)
)
scenario_manager = RolePlayingScenarioGenerator(ChatOpenAI(model="gpt-4o", temperature=0.5))
