from fastapi import APIRouter, Depends, HTTPException
from api.models import FeedbackRequest
from api.auth import has_role, get_current_user
from api.globals import feedbacks, oauth2_scheme

router = APIRouter()

@router.post("/")
@has_role(allowed_roles=["user", "admin"])
def create_feedback(
    feedback_data: FeedbackRequest,
    user=Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    feedback = feedbacks.create_feedback(user, feedback_data.star, feedback_data.review)
    return {"feedback": {"star": feedback.star, "review": feedback.review}}


@router.get("/")
@has_role(allowed_roles=["user", "admin"])
def get_feedback(
    token: str = Depends(oauth2_scheme), user=Depends(get_current_user)
):
    if feedback := feedbacks.get_feedback_by_user(user):
        return {"feedback": {"star": feedback.star, "review": feedback.review}}
    raise HTTPException(status_code=404, detail="Feedback not found")


@router.put("/")
@has_role(allowed_roles=["user", "admin"])
def update_feedback(
    feedback_data: FeedbackRequest,
    token: str = Depends(oauth2_scheme),
    user=Depends(get_current_user),
):
    if feedback := feedbacks.update_feedback(
        user, feedback_data.star, feedback_data.review
    ):
        return {"feedback": {"star": feedback.star, "review": feedback.review}}
    raise HTTPException(status_code=404, detail="Feedback not found")


@router.delete("/")
@has_role(allowed_roles=["user", "admin"])
def delete_feedback(
    user=Depends(get_current_user), token: str = Depends(oauth2_scheme)
):
    if success := feedbacks.delete_feedback(user):
        return {"message": "Feedback deleted successfully"}
    raise HTTPException(status_code=404, detail="Feedback not found")


@router.get("/all")
@has_role(allowed_roles=["admin"])
def get_all_feedbacks(token: str = Depends(oauth2_scheme)):
    all_feedbacks = feedbacks.get_all_feedbacks()
    return {
        "feedbacks": [
            {"star": feedback.star, "review": feedback.review}
            for feedback in all_feedbacks
        ]
    }