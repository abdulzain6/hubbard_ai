from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException
from api.models import GenerateScenarioRequest, EvaluateScenarioRequest
from api.auth import has_role, get_current_user
from api.globals import oauth2_scheme, scenario_manager, scenario_database, user_manager
from api.models import ScenarioCreateRequest, ScenarioUpdateRequest
from api.lib.ai import Scenario, ScenarioEvaluationResult


router = APIRouter()

def grade_to_score(grade: str) -> int:
    grade = grade.upper().strip()
    grade_to_score_mapping = {
        "A+": 5,
        "A": 4,
        "A-": 3,
        "B+": 2,
        "B": 1,
        "B-": 0,
        "C+": -1,
        "C": -2,
        "C-": -3
    }
    
    return grade_to_score_mapping.get(grade, 0)

@router.post("/update_score/")
@has_role(allowed_roles=["admin"])
def update_score(email: str, increment: int, token: str = Depends(oauth2_scheme),) -> dict:
    if user_manager.initialize_or_update_score(email, increment):
        return {"detail": "Score updated successfully"}
    raise HTTPException(status_code=404, detail="User not found")

@router.get("/leaderboard/")
@has_role(allowed_roles=["user", "admin"])
def get_leaderboard(token: str = Depends(oauth2_scheme)):
    return {"leaderboard" : user_manager.get_leaderboard()}

@router.get("/leaderboard_position/")
@has_role(allowed_roles=["user", "admin"])
def get_user_leaderboard_position(current_user = Depends(get_current_user), token: str = Depends(oauth2_scheme)) -> dict:
    position = user_manager.get_user_leaderboard_position(current_user.email)
    if position == -1:
        raise HTTPException(status_code=404, detail="User not found in leaderboard")
    return {"position": position}

@router.post("/generate_scenario", response_model=Scenario)
@has_role(allowed_roles=["admin"])
def generate_scenario(
    request: GenerateScenarioRequest,
    token: str = Depends(oauth2_scheme),
) -> dict[str, str]:
    theme = request.theme
    if result := scenario_manager.generate_scenario(theme=theme):
        return result
    raise HTTPException(status_code=404, detail="Scenario not found")

@router.post("/evaluate_scenario", response_model=ScenarioEvaluationResult)
@has_role(allowed_roles=["user", "admin"])
def evaluate_scenario(
    request: EvaluateScenarioRequest,
    token: str = Depends(oauth2_scheme),
    current_user = Depends(get_current_user)
):

    if scenario := scenario_database.get_scenario_by_name(request.scenario_name):
        if result := scenario_manager.evaluate_scenario(
            scenario=scenario.scenario_description,
            best_response=scenario.best_response,
            explanation=scenario.response_explanation,
            salesman_response=request.salesman_response,
        ):
            score = grade_to_score(result.grade)
            user_manager.initialize_or_update_score(current_user.email, score, request.scenario_name)
            return result
        raise HTTPException(status_code=400, detail="Evaluation not found")
    else:
        raise HTTPException(status_code=400, detail="Scenario not found")


@router.post("/create_scenario")
@has_role(allowed_roles=["admin"])
def create_scenario(request: ScenarioCreateRequest, token: str = Depends(oauth2_scheme)):
    if existing_scenario := scenario_database.get_scenario_by_name(
        request.name
    ):
        raise HTTPException(status_code=400, detail="Scenario already exists")

    try:
        scenario_database.create_scenario(
            name=request.name,
            description=request.description,
            scenario_description=request.scenario_description,
            best_response=request.best_response,
            response_explanation=request.response_explanation,
            difficulty=request.difficulty,
            importance=request.importance
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {e}") from e

    return {"status": "Scenario created successfully!"}

@router.get("/get_scenario/{name}")
@has_role(allowed_roles=["user", "admin"])
def get_scenario(name: str, token: str = Depends(oauth2_scheme)):
    scenario = scenario_database.get_scenario_by_name(name)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario.dict()

@router.put("/update_scenario/{name}")
@has_role(allowed_roles=["admin"])
def update_scenario(name: str, request: ScenarioUpdateRequest, token: str = Depends(oauth2_scheme)):
    existing_scenario = scenario_database.get_scenario_by_name(name)
    if existing_scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    scenario_database.update_scenario(name, request.model_dump(exclude_unset=True))
    return {"status": "Scenario updated successfully!"}

@router.delete("/delete_scenario/{name}")
@has_role(allowed_roles=["admin"])
def delete_scenario(name: str, token: str = Depends(oauth2_scheme)):
    existing_scenario = scenario_database.get_scenario_by_name(name)
    if existing_scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    scenario_database.delete_scenario(name)
    return {"status": "Scenario deleted successfully!"}

@router.get("/get_all_scenarios")
@has_role(allowed_roles=["user", "admin"])
def get_all_scenarios(token: str = Depends(oauth2_scheme)):
    scenarios = scenario_database.get_all_scenarios()
    return [scenario.dict() for scenario in scenarios]