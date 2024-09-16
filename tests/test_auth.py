from app.auth import verify_token
import jwt
from dotenv import load_dotenv
import os
from fastapi import HTTPException

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

def test_valid_token():
    token = jwt.encode({"user_id": 1}, SECRET_KEY, algorithm="HS256")
    payload = verify_token(token)
    assert payload["user_id"] == 1

def test_invalid_token():
    invalid_token = "invalidtoken"
    try:
        verify_token(invalid_token)
    except HTTPException as e:
        assert e.status_code == 401
        assert e.detail == "Invalid token"
    except jwt.DecodeError:
        assert True  
    else:
        assert False
