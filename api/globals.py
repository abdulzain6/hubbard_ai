import contextlib
from .lib.database import (
    Users,
    FileManager,
    PromptHandler,
    ResponseStorer,
    RoleManager,
    SalesRoleplayScenarioManager
)
from .lib.ai import KnowledgeManager, RolePlayingScenarioGenerator
from peewee import PostgresqlDatabase
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from langchain_openai import ChatOpenAI
from .settings import *

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

db = PostgresqlDatabase(
    DATABASE_NAME,
    user=DATABASE_USER,
    password=DATABASE_PASSWORD,
    host=DATABASE_HOST,
    port=DATABASE_PORT,
    autorollback=True, 
    autoconnect=True
)
prompt_handler = PromptHandler(db)
user_manager = Users(db)


manager = KnowledgeManager(
    openai_api_key=OPENAI_API_KEY,
    prompt_handler=prompt_handler,
    response_handler=ResponseStorer(db),
    qdrant_url=QDRANT_URL,
    qdrant_api_key=QDRANT_API_KEY,
    unstructured_api_url=UNSTRUCTURED_URL,
    unstructured_api_key=UNSTRUCTURED_API_KEY,
    collection_name="books_real_main",
    llm=ChatOpenAI(model=GLOBAL_MODEL, temperature=1)
)

with contextlib.suppress(Exception):
    user_manager.create_new_user("abdulzain6@gmail.com", "zainZain123", "admin", "Zain", "pakistan", "123")

response_storer = ResponseStorer(db)
scenario_manager = RolePlayingScenarioGenerator(ChatOpenAI(model="gpt-4o", temperature=0.5))
role_manager = RoleManager(db)
file_manager = FileManager(db)
scenario_database = SalesRoleplayScenarioManager(db)