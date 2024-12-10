import logging
import queue
import threading

from typing import Generator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from api.auth import get_user_id_and_role, UserInfo, get_admin_user
from api.globals import scenario_manager, manager, GLOBAL_MODEL
from api.lib.ai import CustomCallback, Scenario, ScenarioEvaluationResult, split_into_chunks
from api.lib.database import SalesRoleplayScenarioManager, ScenarioModel, FileManager
from pydantic import BaseModel
from langchain_openai import ChatOpenAI



router = APIRouter()

    
class GenerateScenarioRequestMetadata(BaseModel):
    scenario: str
    
class GenerateScenarioRequest(BaseModel):
    scenario_name: str
    
class EvaluateScenarioRequest(BaseModel):
    scenario: Scenario
    salesman_response: str
    


@router.post("/add_scenario", response_model=ScenarioModel)
def add_scenario(request: ScenarioModel, user_data: UserInfo = Depends(get_admin_user)):
    scenario_database = SalesRoleplayScenarioManager()
    file_manager = FileManager(user_id=user_data.user_id)
    file_existence = file_manager.check_files_exist(request.file_names)
    missing_files = [file_name for file_name, exists in file_existence.items() if not exists]
    
    if missing_files:
        raise HTTPException(status_code=400, detail=f"Files not found: {', '.join(missing_files)}")
    
    scenario_database.create_or_update_scenario(
        ScenarioModel(
            name=request.name,
            prompt=request.prompt, 
            file_names=request.file_names
        )
    )
    return scenario_database.get_scenario_by_name(request.name)
    
@router.post("/generate_scenario_metadata", response_model=Scenario)
def generate_scenario_metadata(
    request: GenerateScenarioRequestMetadata,
    user_data: UserInfo = Depends(get_user_id_and_role)
    ) -> dict[str, str]:
    result = scenario_manager.generate_scenario_metadata(scenario=request.scenario)
    return result

@router.post("/generate_scenario")
def generate_scenario(
    request: GenerateScenarioRequest,
    user_data: UserInfo = Depends(get_user_id_and_role)
) -> dict[str, str]:
    
    data_queue = queue.Queue(maxsize=-1)
    scenario_database = SalesRoleplayScenarioManager()


    def data_generator() -> Generator[str, None, None]:
        # yield "[START]"
        while True:
            try:
                data = data_queue.get(timeout=60)
                print(data)
                if data is None:
                    # yield "[END]"
                    break
                yield data
            except queue.Empty:
                yield "[TIMEOUT]"
                break

    def callback(data: str) -> None:
        data_queue.put(data)

    def on_end_callback(response: str) -> None:
        ...
        
    def get_scenario():
        try:
            vectorstore = manager.load_vectorstore(manager.collection_name)
            documents = vectorstore.similarity_search(scenario.name, k=2)#, filter={"role" : role})
            data = "\n".join([doc.page_content for doc in documents])
            scenario_manager.generate_scenario(
                theme=request.scenario_name,
                prompt_in=scenario.prompt,
                data=data,
                llm=ChatOpenAI(
                    model=GLOBAL_MODEL,
                    temperature=0.5,
                    streaming=True,
                    callbacks=[CustomCallback(callback=callback, on_end_callback=on_end_callback)]
                )
            )
            callback(None)
        except Exception as e:
            logging.error(f"Error generating scenarios: {e}")
            error_message = "Error in getting response"
            for chunk in split_into_chunks(error_message, 4):
                callback(chunk)
            callback(None)

    if scenario := scenario_database.get_scenario_by_name(request.scenario_name):
        threading.Thread(target=get_scenario).start()
        return StreamingResponse(data_generator())
    else:
        raise HTTPException(status_code=404, detail="Scenario not found")

@router.post("/evaluate_scenario", response_model=ScenarioEvaluationResult)
def evaluate_scenario(
    request: EvaluateScenarioRequest,
    user_data: UserInfo = Depends(get_user_id_and_role)
):
    try:
        if result := scenario_manager.evaluate_scenario(
            scenario=request.scenario.description,
            best_response=request.scenario.best_response,
            explanation=request.scenario.explanation,
            salesman_response=request.salesman_response,
        ):
            return result
    except Exception as e:
        print("Error Evaluating scenario: ", e)
        raise HTTPException(status_code=500, detail="Error Evaluating scenario")

    raise HTTPException(status_code=400, detail="Evaluation not found")

@router.get("/get_scenario/{name}", response_model=ScenarioModel)
def get_scenario(
    name: str,
    user_data: UserInfo = Depends(get_user_id_and_role)
):
    scenario_database = SalesRoleplayScenarioManager()
    scenario = scenario_database.get_scenario_by_name(name)
    if scenario:
        return scenario
    raise HTTPException(status_code=404, detail="Scenario not found")

@router.put("/update_scenario/{name}", response_model=ScenarioModel)
def update_scenario(
    name: str, 
    attributes: ScenarioModel, 
    user_data: UserInfo = Depends(get_admin_user)
):
    scenario_database = SalesRoleplayScenarioManager()
    file_manager = FileManager(user_id=user_data.user_id)

    scenario = scenario_database.get_scenario_by_name(name)
    file_existence = file_manager.check_files_exist(attributes.file_names)
    missing_files = [file_name for file_name, exists in file_existence.items() if not exists]
    
    if missing_files:
        raise HTTPException(status_code=400, detail=f"Files not found: {', '.join(missing_files)}")
    
    if scenario:
        scenario_database.create_or_update_scenario(
            ScenarioModel(
                name=attributes.name,
                prompt=attributes.prompt,
                file_names=attributes.file_names
            )
        )
        return scenario_database.get_scenario_by_name(name)
    raise HTTPException(status_code=404, detail="Scenario not found")

@router.delete("/delete_scenario/{name}", response_model=dict)
def delete_scenario(name: str, user_data: UserInfo = Depends(get_admin_user)):
    scenario_database = SalesRoleplayScenarioManager()
    scenario = scenario_database.get_scenario_by_name(name)
    if scenario:
        scenario_database.delete_scenario(name)
        return {"detail": "Scenario deleted successfully"}
    raise HTTPException(status_code=404, detail="Scenario not found")

@router.get("/get_all_scenarios", response_model=list[ScenarioModel])
def get_all_scenarios(user_data: UserInfo = Depends(get_user_id_and_role)):
    scenario_database = SalesRoleplayScenarioManager()
    return scenario_database.get_all_scenarios()
