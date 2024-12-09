from dotenv import load_dotenv
import os


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GLOBAL_MODEL = os.getenv("GLOBAL_MODEL", "gpt-4o")