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
    scenario_name: str
    salesman_response: str
    


@router.post("/", response_model=ScenarioModel)
def add_scenario(request: ScenarioModel, user_data: UserInfo = Depends(get_admin_user)):
    scenario_database = SalesRoleplayScenarioManager()
    scenario_database.create_or_update_scenario(
        request
    )
    return scenario_database.get_scenario_by_name(request.name)
    
@router.post("/ai-generate", response_model=Scenario)
def generate_scenario_metadata(
    request: GenerateScenarioRequestMetadata,
    user_data: UserInfo = Depends(get_user_id_and_role)
    ) -> dict[str, str]:
    result = scenario_manager.generate_scenario_metadata(scenario=request.scenario)
    return result

@router.post("/evaluate_scenario", response_model=ScenarioEvaluationResult)
def evaluate_scenario(
    request: EvaluateScenarioRequest,
    user_data: UserInfo = Depends(get_user_id_and_role)
):
    scenario_db = SalesRoleplayScenarioManager()
    scenario = scenario_db.get_scenario_by_name(request.scenario_name)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    try:
        if result := scenario_manager.evaluate_scenario(
            scenario=scenario.description,
            best_response=scenario.best_response,
            explanation=scenario.explanation,
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
    scenario = scenario_database.get_scenario_by_name(name)
    if scenario:
        scenario_database.create_or_update_scenario(
            attributes
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
