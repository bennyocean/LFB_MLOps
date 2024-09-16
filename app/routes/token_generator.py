from fastapi import APIRouter
import jwt
import os

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY")

@router.get("/generate-token")
def generate_token():
    payload = {"user_id": 1}  
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return {"token": token}
