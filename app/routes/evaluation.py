from fastapi import APIRouter, Depends, HTTPException
from app.utils import evaluate_model_on_test_set, log_evaluation_result
from app.auth import verify_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/evaluate", tags=["Model Evaluation"])
async def evaluate_model(token: str = Depends(oauth2_scheme)):
    # Überprüfen des Tokens und Abrufen des Benutzers
    current_user = verify_token(token, required_role="admin")

    try:
        # Bewertung des Modells auf dem Testdatensatz
        accuracy = evaluate_model_on_test_set()

        # Logge die Accuracy ins evaluation.log
        log_evaluation_result(accuracy)

        return {
            "user": current_user,
            "evaluation_result": {
                "accuracy": accuracy
            }
        }
    except Exception as e:
        # Fehlerbehandlung, falls während der Evaluierung etwas schiefgeht
        raise HTTPException(status_code=500, detail=f"Model evaluation failed: {str(e)}")