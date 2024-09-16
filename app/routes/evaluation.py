from fastapi import APIRouter, Depends
from app.auth import verify_token
from app.utils import evaluate_model_on_test_set

router = APIRouter()

@router.get("/evaluate")
def evaluate_model(token: str = Depends(verify_token)):
    accuracy = evaluate_model_on_test_set()

    return {"model_accuracy": accuracy}