from .lib.ai import KnowledgeManager, RolePlayingScenarioGenerator
from .settings import *
from langchain_openai import ChatOpenAI


manager = KnowledgeManager(
    openai_api_key=OPENAI_API_KEY,
    collection_name="books_real_main",
    llm=ChatOpenAI(model=GLOBAL_MODEL, temperature=1)
)
scenario_manager = RolePlayingScenarioGenerator(ChatOpenAI(model="gpt-4o-mini", temperature=0.5))
