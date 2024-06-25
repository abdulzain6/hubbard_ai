from fastapi import APIRouter, Depends, HTTPException
from api.auth import has_role
from api.globals import oauth2_scheme, scenario_manager, scenario_database, file_manager, manager
from api.lib.ai import Scenario, ScenarioEvaluationResult
from pydantic import BaseModel
from playhouse.shortcuts import model_to_dict



router = APIRouter()

    
class GenerateScenarioRequest(BaseModel):
    scenario_name: str
    
    
class EvaluateScenarioRequest(BaseModel):
    scenario: Scenario
    salesman_response: str

class ScenarioResponse(BaseModel):
    name: str
    prompt: str
    file_names: list[str]

class AddScenarioRequest(BaseModel):
    name: str
    prompt: str
    file_names: list[str]

@router.post("/add_scenario", response_model=ScenarioResponse)
@has_role(allowed_roles=["user", "admin"])
def add_scenario(request: AddScenarioRequest, token: str = Depends(oauth2_scheme)):
    file_existence = file_manager.check_files_exist(request.file_names)
    missing_files = [file_name for file_name, exists in file_existence.items() if not exists]
    
    if missing_files:
        raise HTTPException(status_code=400, detail=f"Files not found: {', '.join(missing_files)}")
    
    if scenario_database.create_scenario(name=request.name, prompt=request.prompt, file_names=request.file_names):
        return ScenarioResponse(name=request.name, prompt=request.prompt, file_names=request.file_names)
    
    raise HTTPException(status_code=400, detail="Failed to create scenario")

@router.post("/generate_scenario", response_model=Scenario)
@has_role(allowed_roles=["admin", "user"])
def generate_scenario(
    request: GenerateScenarioRequest,
    token: str = Depends(oauth2_scheme),
) -> dict[str, str]:
    if scenario := scenario_database.get_scenario_by_name(request.scenario_name):
        vectorstore = manager.load_vectorstore(manager.collection_name)
        documents = vectorstore.similarity_search(scenario.name, k=2)#, filter={"role" : role})
        data = "\n".join([doc.page_content for doc in documents])
        if result := scenario_manager.generate_scenario(theme=scenario.name, prompt_in=scenario.prompt, data=data):
            return result
    else:
        raise HTTPException(status_code=404, detail="Scenario not found")

@router.post("/evaluate_scenario", response_model=ScenarioEvaluationResult)
@has_role(allowed_roles=["user", "admin"])
def evaluate_scenario(
    request: EvaluateScenarioRequest,
    token: str = Depends(oauth2_scheme),
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

@router.get("/get_scenario/{name}", response_model=ScenarioResponse)
@has_role(allowed_roles=["user", "admin"])
def get_scenario(name: str, token: str = Depends(oauth2_scheme)):
    scenario = scenario_database.get_scenario_by_name(name)
    if scenario:
        return model_to_dict(scenario)
    raise HTTPException(status_code=404, detail="Scenario not found")

@router.put("/update_scenario/{name}", response_model=ScenarioResponse)
@has_role(allowed_roles=["user", "admin"])
def update_scenario(name: str, attributes: AddScenarioRequest, token: str = Depends(oauth2_scheme)):
    scenario = scenario_database.get_scenario_by_name(name)
    file_existence = file_manager.check_files_exist(attributes.file_names)
    missing_files = [file_name for file_name, exists in file_existence.items() if not exists]
    
    if missing_files:
        raise HTTPException(status_code=400, detail=f"Files not found: {', '.join(missing_files)}")
    
    if scenario:
        scenario_database.update_scenario(name, attributes.model_dump())
        return model_to_dict(scenario_database.get_scenario_by_name(name))
    raise HTTPException(status_code=404, detail="Scenario not found")

@router.delete("/delete_scenario/{name}", response_model=dict)
@has_role(allowed_roles=["user", "admin"])
def delete_scenario(name: str, token: str = Depends(oauth2_scheme)):
    scenario = scenario_database.get_scenario_by_name(name)
    if scenario:
        scenario_database.delete_scenario(name)
        return {"detail": "Scenario deleted successfully"}
    raise HTTPException(status_code=404, detail="Scenario not found")

@router.get("/get_all_scenarios", response_model=list[ScenarioResponse])
@has_role(allowed_roles=["user", "admin"])
def get_all_scenarios(token: str = Depends(oauth2_scheme)):
    scenarios = scenario_database.get_all_scenarios()
    return [model_to_dict(scenario) for scenario in scenarios]