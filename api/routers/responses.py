from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from ..auth import get_current_user, has_role
from ..globals import oauth2_scheme, response_storer

from pydantic import BaseModel

class ResponseData(BaseModel):
    prompt: str
    response: str

class RankData(BaseModel):
    prompt: str
    rank: int
    from_rank: int

class UpdateRankData(BaseModel):
    prompt: str
    rank: int
    attributes: dict

router = APIRouter()

@router.post("/create_response", response_model=ResponseData, status_code=status.HTTP_201_CREATED)
@has_role(allowed_roles=["admin"])
def create_response(response_data: ResponseData, user=Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    try:
        response_storer.create_new_response(prompt=response_data.prompt, response=response_data.response)
        return response_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create response: {str(e)}")

@router.post("/set_rank")
@has_role(allowed_roles=["admin"])
def set_response_rank(rank_data: RankData, user=Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    try:
        success = response_storer.set_rank(prompt=rank_data.prompt, rank=rank_data.rank, from_rank=rank_data.from_rank)
        if not success:
            raise HTTPException(status_code=404, detail="Operation failed or invalid rank")
        return {"message": "Rank updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to set rank: {str(e)}")

@router.put("/update_response")
@has_role(allowed_roles=["admin"])
def update_response(update_data: UpdateRankData, user=Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    try:
        response_storer.update_resp(prompt=update_data.prompt, rank=update_data.rank, attributes=update_data.attributes)
        return {"message": "Response updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update response: {str(e)}")

@router.delete("/delete_response/{prompt}/{rank}", status_code=status.HTTP_204_NO_CONTENT)
@has_role(allowed_roles=["admin"])
def delete_response(prompt: str, rank: int, user=Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    try:
        response_storer.delete_resp(prompt, rank)
        return {"message": "Response deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Failed to delete response: {str(e)}")

@router.get("/responses/{prompt}")
@has_role(allowed_roles=["admin"])
def get_responses(prompt: str, user=Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    try:
        responses = response_storer.get_all_responses_by_prompt(prompt)
        return responses
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch responses: {str(e)}")
