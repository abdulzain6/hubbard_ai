from langchain_community.document_loaders import UnstructuredAPIFileLoader
from langchain_community.document_loaders import UnstructuredFileLoader
file_path = '/home/zain/work/hubbard_ai_upload_files/Hubbard.ai Training Content/Duplicate Books/You Can_t Teach a Kid to Ride a Bike at a Seminar.pdf'
loader = UnstructuredAPIFileLoader(
    file_path=file_path,
    api_key="",
    url="http://localhost:8001",
    strategy="fast",
    mode="single"
)
print(loader.load())