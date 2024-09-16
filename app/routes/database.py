from fastapi import APIRouter, Depends
from app.auth import verify_token
from app.models import NewData
import logging

router = APIRouter()

@router.post("/database/add")
def add_data(new_data: NewData, token: str = Depends(verify_token)):
    # Simulate adding data to the database
    logging.info(f"New data added: {new_data}")
    return {"message": "Data added successfully"}
