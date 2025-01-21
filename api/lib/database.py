import uuid
import firebase_admin
from typing import List, Optional
from pydantic import BaseModel, Field
from firebase_admin import credentials, initialize_app, firestore


class FileModel(BaseModel):
    file_name: str = Field(..., description="Unique identifier for the file")
    description: Optional[str] = Field(None, description="Description of the file")
    content: Optional[str] = Field(None, description="Content of the file")
    vector_ids: List[str] = Field(default_factory=list, description="List of vector IDs")

class ScenarioModel(BaseModel):
    name: str = Field(..., description="Unique identifier for the scenario")
    prompt: str = Field(..., description="Prompt for the scenario")
    file_names: List[str] = Field(..., description="List of file names associated with the scenario")

class RoleModel(BaseModel):
    name: str = Field(..., description="Unique identifier for the role")
    prompt_prefix: str = Field(..., description="Prompt prefix for the role")
    
class ChatHistoryModel(BaseModel):
    chat_session_id: str = Field(..., description="Unique identifier for the chat session")
    user_id: str = Field(..., description="ID of the user")
    topic: str = Field(..., description="Topic of the chat session")
    chat_history: List[tuple[str, str]] = Field(default_factory=list, description="List of tuples containing chat messages")


class FileManager:
    def __init__(self, user_id: str, credentials_path: Optional[str] = None):
        if credentials_path:
            cred = credentials.Certificate(credentials_path)
        else:
            cred = None
        if not firebase_admin._apps:
            initialize_app(cred)

        self.db = firestore.client()
        self.user_id = user_id
        
        user_doc_ref = self.db.collection('users').document(user_id)
        if not user_doc_ref.get().exists:
            user_doc_ref.set({})
        self.collection = user_doc_ref.collection('files')
        
    def check_files_exist(self, file_names: List[str]) -> dict[str, bool]:
        file_statuses = {}
        for file_name in file_names:
            doc_ref = self.collection.document(file_name)
            file_statuses[file_name] = doc_ref.get().exists
        return file_statuses
    
    def create_or_update_file(self, file: FileModel):
        doc_ref = self.collection.document(file.file_name)
        doc_ref.set(file.dict(), merge=True)

    def read_file(self, file_name: str) -> Optional[FileModel]:
        doc_ref = self.collection.document(file_name)
        doc = doc_ref.get()
        if doc.exists:
            return FileModel(**doc.to_dict())
        return None

    def delete_file(self, file_name: str):
        doc_ref = self.collection.document(file_name)
        doc_ref.delete()

    def get_all_files(self) -> List[FileModel]:
        docs = self.collection.stream()
        return [FileModel(**doc.to_dict()) for doc in docs]

class RoleManager:
    def __init__(self, credentials_path: Optional[str] = None):
        if credentials_path:
            cred = credentials.Certificate(credentials_path)
        else:
            cred = None

        if not firebase_admin._apps:
            initialize_app(cred)
        
        self.db = firestore.client()
        self.collection = self.db.collection('roles')

    def create_or_update_role(self, role: RoleModel) -> None:
        doc_ref = self.collection.document(role.name)
        doc_ref.set(role.model_dump(), merge=True)

    def read_role(self, name: str) -> Optional[RoleModel]:
        doc_ref = self.collection.document(name)
        doc = doc_ref.get()
        if doc.exists:
            return RoleModel(**doc.to_dict())
        return None

    def delete_role(self, name: str) -> None:
        doc_ref = self.collection.document(name)
        doc_ref.delete()

    def get_all_roles(self) -> List[RoleModel]:
        docs = self.collection.stream()
        return [RoleModel(**doc.to_dict()) for doc in docs]

class SalesRoleplayScenarioManager:
    def __init__(self, credentials_path: Optional[str] = None):
        if credentials_path:
            cred = credentials.Certificate(credentials_path)
        else:
            cred = None
            
        if not firebase_admin._apps:
            initialize_app(cred)

        self.db = firestore.client()
        self.collection = self.db.collection('scenarios')
        
    def create_or_update_scenario(self, scenario: ScenarioModel) -> None:
        doc_ref = self.collection.document(scenario.name)
        doc_ref.set(scenario.model_dump(), merge=True)

    def get_scenario_by_name(self, name: str) -> Optional[ScenarioModel]:
        doc_ref = self.collection.document(name)
        doc = doc_ref.get()
        if doc.exists:
            return ScenarioModel(**doc.to_dict())
        return None
        
    def delete_scenario(self, name: str) -> None:
        doc_ref = self.collection.document(name)
        doc_ref.delete()

    def get_all_scenarios(self) -> List[ScenarioModel]:
        docs = self.collection.stream()
        return [ScenarioModel(**doc.to_dict()) for doc in docs]

class ChatHistoryManager:
    def __init__(self, credentials_path: Optional[str] = None):
        if credentials_path:
            cred = credentials.Certificate(credentials_path)
        else:
            cred = None
            
        if not firebase_admin._apps:
            initialize_app(cred)

        self.db = firestore.client()
        self.collection = self.db.collection('chat_history')

    def _generate_doc_id(self, user_id: str, chat_session_id: str) -> str:
        """Generates a document ID by combining user_id and chat_session_id"""
        return f"{user_id}_{chat_session_id}"

    def create_or_update_conversation(self, chat: ChatHistoryModel) -> None:
        """Creates or updates a chat conversation"""
        doc_id = self._generate_doc_id(chat.user_id, chat.chat_session_id)
        doc_ref = self.collection.document(doc_id)
        doc = doc_ref.get()
        if not doc.exists:
            # Convert tuples to dictionaries for Firestore storage
            chat_dict = chat.model_dump()
            chat_dict['chat_history'] = [{'human': msg[0], 'ai': msg[1]} for msg in chat.chat_history]
            doc_ref.set(chat_dict)
        else:
            raise ValueError("Chat already exists")

    def get_conversation(self, chat_session_id: str, user_id: str) -> Optional[ChatHistoryModel]:
        """Gets a specific conversation by chat_session_id and validates user_id"""
        doc_id = self._generate_doc_id(user_id, chat_session_id)
        doc_ref = self.collection.document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            chat_data = doc.to_dict()
            if chat_data.get('user_id') == user_id:
                # Convert dictionary messages back to tuples
                chat_data['chat_history'] = [(msg['human'], msg['ai']) for msg in chat_data['chat_history']]
                return ChatHistoryModel(**chat_data)
        return None

    def get_user_conversations(self, user_id: str) -> List[ChatHistoryModel]:
        """Gets all conversations for a specific user"""
        docs = self.collection.where('user_id', '==', user_id).stream()
        conversations = []
        for doc in docs:
            chat_data = doc.to_dict()
            # Convert dictionary messages back to tuples
            chat_data['chat_history'] = [(msg['human'], msg['ai']) for msg in chat_data['chat_history']]
            conversations.append(ChatHistoryModel(**chat_data))
        return conversations

    def delete_conversation(self, chat_session_id: str, user_id: str) -> None:
        """Deletes a conversation by chat_session_id if it belongs to the user"""
        doc_id = self._generate_doc_id(user_id, chat_session_id)
        doc_ref = self.collection.document(doc_id)
        doc = doc_ref.get()
        if doc.exists and doc.to_dict().get('user_id') == user_id:
            doc_ref.delete()

    def add_message(self, chat_session_id: str, user_id: str, human_message: str, ai_message: str) -> None:
        """Adds a message to an existing conversation if it belongs to the user"""
        doc_id = self._generate_doc_id(user_id, chat_session_id)
        doc_ref = self.collection.document(doc_id)
        doc = doc_ref.get()
        if doc.exists and doc.to_dict().get('user_id') == user_id:
            doc_ref.update({
                'chat_history': firestore.ArrayUnion([{
                    'human': human_message,
                    'ai': ai_message
                }])
            })
