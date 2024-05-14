from fastapi import APIRouter, Depends, HTTPException
from api.auth import has_role
from api.globals import oauth2_scheme, scenario_manager
from api.lib.ai import Scenario, ScenarioEvaluationResult
from pydantic import BaseModel



router = APIRouter()

    
class GenerateScenarioRequest(BaseModel):
    theme: str
    
class EvaluateScenarioRequest(BaseModel):
    scenario: Scenario
    salesman_response: str


@router.post("/generate_scenario", response_model=Scenario)
@has_role(allowed_roles=["admin", "user"])
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
