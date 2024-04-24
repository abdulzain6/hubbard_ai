import contextlib
import json
import logging
from datetime import datetime
from peewee import *
from playhouse.shortcuts import model_to_dict
from passlib.context import CryptContext
from langchain_core.prompts import PromptTemplate
from peewee import Model, CharField, ForeignKeyField, IntegerField, SqliteDatabase
from typing import Dict, List, Optional, Union


class FileManager:
    def __init__(self, db: SqliteDatabase):
        class File(Model):
            file_name = CharField(primary_key=True, unique=True)
            description = CharField(null=True)
            content = TextField(null=True)
            vector_ids = TextField(null=True)  # Store vector_ids as JSON serialized string

            class Meta:
                database = db

        self.model = File
        self.db = db
        db.connect(reuse_if_open=True)
        db.create_tables([File], safe=True)

    def create_file(
        self, file_name: str, description: str, content: str, vector_ids: list
    ):
        with self.db.connection_context():
            with contextlib.suppress(IntegrityError):
                file = self.model(
                    file_name=file_name,
                    description=description,
                    content=content,
                    vector_ids=json.dumps(vector_ids)  # Serialize the list to a JSON string
                )
                file.save(force_insert=True)

    def read_file(self, file_name: str):
        with self.db.connection_context():
            try:
                file = self.model.get(self.model.file_name == file_name)
                file.vector_ids = json.loads(file.vector_ids) if file.vector_ids else []
                return file
            except self.model.DoesNotExist:
                return None

    def update_file(self, file_name: str, attributes: dict):
        with self.db.connection_context():
            file = self.model.get(self.model.file_name == file_name)
            for attr, value in attributes.items():
                if attr == 'vector_ids' and isinstance(value, list):
                    value = json.dumps(value)  # Serialize list to JSON before saving
                setattr(file, attr, value)
            file.save()

    def delete_file(self, file_name: str):
        with self.db.connection_context():
            file = self.model.get(self.model.file_name == file_name)
            file.delete_instance()

    def get_all_files(self) -> list:
        with self.db.connection_context():
            files = self.model.select()
            files_list = []
            for file in files:
                # Deserialize the vector_ids field into a list
                vector_ids_list = json.loads(file.vector_ids) if file.vector_ids else []
                # Create a dictionary for each file and append it to the list
                file_dict = {
                    "file_name": file.file_name,
                    "description": file.description,
                    "content": file.content,
                    "vector_ids": vector_ids_list
                }
                files_list.append(file_dict)
            return files_list

    def get_cls(self):
        return self.model

class PromptHandler:
    def __init__(self, db: SqliteDatabase, prompt_variables: list[str] = None):
        class Prompt(Model):
            name = CharField(primary_key=True, unique=True)
            last_updated = DateTimeField()
            is_main = BooleanField()
            content = TextField()

            class Meta:
                database = db

        self.model = Prompt
        self.db = db
        db.connect(reuse_if_open=True)
        db.create_tables([Prompt], safe=True)
        self.prompt_variables = prompt_variables or [
            "insights",
            "human_question",
            "data",
            "chat_history",
            "role",
            "job",
            "company",
            "department",
            "company_role",
            "prompt_prefix"
        ]

    def validate_prompt(self, prompt: str) -> bool:
        try:
            PromptTemplate(template=prompt, input_variables=self.prompt_variables, validate_template=True)
            return True
        except Exception:
            return False

    def get_prompt_by_name(self, name: str):
        with self.db.connection_context():
            try:
                return self.model.get(self.model.name == name)
            except DoesNotExist:
                return None

    def create_prompt(self, name: str, is_main: bool, content: str):
        with self.db.connection_context():
            with contextlib.suppress(Exception):
                prompt = self.model(
                    name=name,
                    is_main=is_main,
                    last_updated=datetime.now(),
                    content=content,
                )
                prompt.save(force_insert=True)

    def update_prompt(self, name: str, attributes: dict):
        with self.db.connection_context():
            prompt = self.model.get(self.model.name == name)
            if not prompt:
                logging.error("Prompt not found on update")
                raise ValueError("Prompt not found")
            for attr, value in attributes.items():
                setattr(prompt, attr, value)
            prompt.save()

    def delete_prompt(self, name: str):
        with self.db.connection_context():
            prompt = self.model.get(self.model.name == name)
            prompt.delete_instance()

    def get_all_prompts(self) -> list:
        with self.db.connection_context():
            return [model_to_dict(prompt) for prompt in list(self.model.select())]

    def get_cls(self):
        return self.model

    def get_main_prompt(self):
        try:
            with self.db.connection_context():
                return list(self.model.select().where(self.model.is_main == True))[0]
        except IndexError:
            return None

    def choose_main_prompt(self, name: str):
        with self.db.connection_context():
            if main := self.get_main_prompt():
                self.update_prompt(main.name, {"is_main": False})
            self.update_prompt(name, {"is_main": True})

class ResponseStorer:
    def __init__(self, db: SqliteDatabase):
        class Response(Model):
            rank = IntegerField()
            prompt = TextField()
            response = TextField()

            class Meta:
                database = db

        self.model = Response
        self.db = db
        db.connect(reuse_if_open=True)
        db.create_tables([Response], safe=True)

    def get_highest_rank_response(self, prompt: str):
        with self.db.connection_context():
            query = (
                self.model.select()
                .where(self.model.prompt == prompt)
                .order_by(self.model.rank.asc())
                .limit(1)
            )
            return query.get() if query.exists() else None

    def get_max_rank(self, prompt):
        with self.db.connection_context():
            if query := self.model.select(self.model.rank).where(
                self.model.prompt == prompt
            ):
                return max(resp.rank for resp in list(query))
            else:
                return 0

    def create_new_response(self, prompt: str, response: str):
        with self.db.connection_context():
            rank = self.get_max_rank(prompt) + 1
            with contextlib.suppress(Exception):
                resp = self.model(prompt=prompt, response=response, rank=rank)
                resp.save(force_insert=True)

    def set_rank(self, prompt: str, rank: int, from_rank: str) -> bool:
        with self.db.connection_context():
            to_change = self.model.select().where(
                self.model.prompt == prompt and self.model.rank == from_rank
            )
            if not to_change:
                return False

            if to_replace := self.model.select().where(
                self.model.prompt == prompt and self.model.rank == rank
            ):
                to_change_rank = to_change[0].rank
                to_replace_rank = to_replace[0].rank
                self.update_resp(prompt, from_rank, {"rank": to_replace_rank})
                self.update_resp(prompt, rank, {"rank": to_change_rank})
            else:
                self.update_resp(prompt, from_rank, {"rank": rank})
            return True

    def update_resp(self, prompt: str, rank: int, attributes: dict):
        with self.db.connection_context():
            resp = self.model.get(
                self.model.prompt == prompt and self.model.rank == rank
            )
            for attr, value in attributes.items():
                setattr(resp, attr, value)
            resp.save()

    def delete_resp(self, prompt: str, rank: int):
        with self.db.connection_context():
            resp = self.model.get(
                self.model.prompt == prompt and self.model.rank == rank
            )
            resp.delete_instance()

    def get_all_responses(self) -> list:
        with self.db.connection_context():
            return list(self.model.select())

    def get_cls(self):
        return self.model

    def get_all_responses_by_prompt(self, prompt: str) -> list:
        with self.db.connection_context():
            return list(self.model.select().where(self.model.prompt == prompt))

class Users:
    def __init__(self, db: SqliteDatabase):
        class User(Model):
            email: str = CharField(unique=True, primary_key=True)
            password_hash: str = CharField()
            role: str = CharField()
            name: str = CharField(null=True)  # Name of the user
            country: str = CharField(null=True)  # Country of the user
            phone: str = CharField(null=True)  # Phone number of the user
            company: str = CharField(null=True)  # Company of the user
            department: str = CharField(null=True)  # Department of the user
            company_role: str = CharField(null=True)

            def dict(self) -> dict:
                return {
                    "email": self.email,
                    "name": self.name,
                    "country": self.country,
                    "phone": self.phone,
                    "company": self.company,
                    "department": self.department,
                    "company_role" : self.company_role
                }

            class Meta:
                database = db

        class Leaderboard(Model):
            user = ForeignKeyField(User, backref='score', unique=True, on_delete='CASCADE')
            score = IntegerField()
            
            class Meta:
                database = db

        class UserQuestion(Model):
            user = ForeignKeyField(User, backref='answered_questions')
            question_id = TextField()

            class Meta:
                database = db
                indexes = (
                    (('user', 'question_id'), True),
                )
                
                
        self.user_question_model = UserQuestion
        self.leaderboard_model = Leaderboard
        self.model = User
        self.db = db
        db.connect(reuse_if_open=True)
        db.create_tables([User, Leaderboard, UserQuestion], safe=True)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def get_user_by_email(self, email: str):
        with self.db.connection_context():
            try:
                return self.model.get(self.model.email == email)
            except self.model.DoesNotExist:
                return None

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_new_user(
        self,
        email: str,
        password: str,
        role: str,
        name: str,
        country: str,
        phone: str,
        company: Optional[str] = None,
        department: Optional[str] = None,
        company_role: Optional[str] = None
    ) -> bool:
        with self.db.connection_context():
            user = self.model(
                email=email,
                password_hash=self.hash_password(password),
                role=role,
                name=name,
                country=country,
                phone=phone,
                company=company,
                department=department,
                company_role=company_role
            )
            user.save(force_insert=True)
            return True

    def update_user(self, email: str, attributes: Dict[str, Optional[str]]) -> None:
        logging.debug(f"Email {email} Attr: {attributes}")
        with self.db.connection_context():
            user = self.model.get(self.model.email == email)
            for attr, value in attributes.items():
                if attr == "password":
                    logging.debug("Hashing password")
                    value = self.hash_password(value)
                    setattr(user, 'password_hash', value)
                else:
                    setattr(user, attr, value)
            user.save()

    def delete_user(self, email: str) -> None:
        with self.db.connection_context():
            resp = self.model.get(self.model.email == email)
            resp.delete_instance()

    def get_all_users(self) -> list:
        with self.db.connection_context():
            return list(self.model.select())

    def get_cls(self):
        return self.model

    def initialize_or_update_score(self, email: str, increment: int, question_id: int) -> bool:
        with self.db.connection_context():
            user, _ = self.model.get_or_create(email=email)
            leaderboard_entry, _ = self.leaderboard_model.get_or_create(user=user, defaults={'score': 0})
            
            # Check if this question has been answered by the user before
            user_question, created = self.user_question_model.get_or_create(
                user=user, 
                question_id=question_id
            )
            if not created:
                return False
            
            # Update leaderboard score
            leaderboard_entry.score += increment
            leaderboard_entry.save()
            
            return True

    def get_leaderboard(self) -> List[Dict[str, int]]:
        with self.db.connection_context():
            return [(entry.user.email, entry.score) for entry in self.leaderboard_model.select().order_by(self.leaderboard_model.score.desc())]

    def get_user_leaderboard_position(self, email: str) -> int:
        with self.db.connection_context():
            user = self.model.get(self.model.email == email)
            scores = self.leaderboard_model.select().order_by(self.leaderboard_model.score.desc())
            return next(
                (
                    index + 1
                    for index, score_entry in enumerate(scores)
                    if score_entry.user == user
                ),
                -1,
            )

class RoleManager:
    def __init__(
        self, db
    ):
        class Role(Model):
            name = CharField()
            prompt_prefix = TextField()

            class Meta:
                database = db

        self.model = Role
        self.db = db

        db.connect(reuse_if_open=True)
        db.create_tables([Role], safe=True)

    def create_role(
        self, name: str, prompt: str
    ):
        with self.db.connection_context():
            role = self.model(
                name=name, prompt_prefix=prompt
            )
            role.save(force_insert=True)

    def read_role(self, name: str):
        with self.db.connection_context():
            try:
                return self.model.get(
                    (self.model.name == name)
                )
            except DoesNotExist:
                return None

    def update_role(
        self, name: str, new_name: str
    ):
        with self.db.connection_context():
            role = self.model.get(
                (self.model.name == name)
            )
            role.name = new_name
            role.save()

    def delete_role(self, name: str):
        with self.db.connection_context():
            role = self.model.get(
                (self.model.name == name)
            )
            role.delete_instance()

    def get_all_roles(self) -> list:
        with self.db.connection_context():
            return list(
                self.model.select()
            )

class SalesRoleplayScenarioManager:
    def __init__(self, db: SqliteDatabase):
        class Scenario(Model):
            name = CharField(unique=True, primary_key=True)  # Scenario name
            description = TextField()  # Scenario description
            scenario_description = TextField()  # Scenario description
            best_response = TextField()  # Best response
            response_explanation = TextField()  # Response explanation
            difficulty = TextField(
                constraints=[Check("difficulty IN ('A', 'B', 'C')")]
            )  # Difficulty level
            importance = IntegerField(
                constraints=[Check("importance IN (1, 2, 3)")]
            )  # Importance level

            class Meta:
                database = db

            def dict(self) -> dict:
                return {
                    "name": self.name,
                    "description": self.description,
                    "scenario_description": self.scenario_description,
                    "best_response": self.best_response,
                    "response_explanation": self.response_explanation,
                    "difficulty": self.difficulty,
                    "importance": self.importance,
                }

        self.model = Scenario
        self.db = db
        db.connect(reuse_if_open=True)
        db.create_tables([Scenario], safe=True)

    def create_scenario(
        self,
        name: str,
        description: str,
        scenario_description: str,
        best_response: str,
        response_explanation: str,
        difficulty: str,
        importance: int,
    ) -> bool:
        with self.db.connection_context():
            scenario = self.model(
                name=name,
                description=description,
                scenario_description=scenario_description,
                best_response=best_response,
                response_explanation=response_explanation,
                difficulty=difficulty,
                importance=importance,
            )
            scenario.save(force_insert=True)
            return True

    def get_scenario_by_name(self, name: str):
        with self.db.connection_context():
            try:
                return self.model.get(self.model.name == name)
            except self.model.DoesNotExist:
                return None

    def update_scenario(self, name: str, attributes: dict) -> None:
        with self.db.connection_context():
            scenario = self.model.get(self.model.name == name)
            for attr, value in attributes.items():
                setattr(scenario, attr, value)
            scenario.save()

    def delete_scenario(self, name: str) -> None:
        with self.db.connection_context():
            resp = self.model.get(self.model.name == name)
            resp.delete_instance()

    def get_all_scenarios(self) -> list:
        with self.db.connection_context():
            return list(self.model.select())

    def get_cls(self):
        return self.model

class FeedbackHandler:
    def __init__(self, db: SqliteDatabase, user_model: Model):
        class Feedback(Model):
            user = ForeignKeyField(
                user_model, backref="feedback", unique=True
            )  # One-to-one relation to User
            star = IntegerField()  # Assuming stars are from 1 to 5
            review = TextField()

            class Meta:
                database = db

        self.model = Feedback
        self.db = db
        db.connect(reuse_if_open=True)
        db.create_tables([Feedback], safe=True)

    def create_feedback(self, user: Union[str, Model], star: int, review: str) -> Model:
        if star < 1 or star > 5:
            raise ValueError("Star rating must be between 1 and 5")

        with self.db.connection_context():
            feedback = self.model(user=user, star=star, review=review)
            feedback.save(force_insert=True)
            return feedback

    def update_feedback(
        self,
        user: Union[str, Model],
        star: Optional[int] = None,
        review: Optional[str] = None,
    ) -> Optional[Model]:
        if star and (star < 1 or star > 5):
            raise ValueError("Star rating must be between 1 and 5")

        with self.db.connection_context():
            feedback = self.get_feedback_by_user(user)
            if not feedback:
                return None

            if star:
                feedback.star = star
            if review:
                feedback.review = review
            feedback.save()
            return feedback

    def get_feedback_by_user(self, user: Union[str, Model]) -> Optional[Model]:
        with self.db.connection_context():
            try:
                return self.model.get(self.model.user == user)
            except self.model.DoesNotExist:
                return None

    def delete_feedback(self, user: Union[str, Model]) -> bool:
        with self.db.connection_context():
            if feedback := self.get_feedback_by_user(user):
                feedback.delete_instance()
                return True
            return False

    def get_all_feedbacks(self) -> List[Model]:
        with self.db.connection_context():
            return list(self.model.select())


if __name__ == "__main__":
    users = FileManager(SqliteDatabase("database/database.db"))
    users.create_new_user(
        "abdulzain6@gmail.com", "zainZain123", "admin", "Zain", "pakistan", "123"
    )
