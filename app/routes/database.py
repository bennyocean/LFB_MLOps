from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.security import OAuth2PasswordBearer
from app.db import db
from app.auth import verify_token
from typing import Optional, Dict


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Helper function to convert MongoDB document ObjectId to string
def object_id_to_str(doc):
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc


@router.get("/data", tags=["MongoDB"])
async def read_data(token: str = Depends(oauth2_scheme)):
    current_user = verify_token(token)  # Verify the JWT token, but don't restrict by role

    try:
        data = list(db.lfb.find().limit(5))  # Read 15 documents for now
        if not data:
            raise HTTPException(status_code=404, detail="No data found in lfb.lfb")
        
        # Convert ObjectId to string for each document
        data = [object_id_to_str(doc) for doc in data]
        
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/{sample_id}", tags=["MongoDB"])
async def get_data(sample_id: str, token: str = Depends(oauth2_scheme)):
    current_user = verify_token(token)  # Verify the token, no role restriction

    try:
        # Convert the sample_id (string) into ObjectId
        object_id = ObjectId(sample_id)
        db_entry = db.lfb.find_one({"_id": object_id})

        if not db_entry:
            raise HTTPException(status_code=404, detail="Data not found")

        # Convert ObjectId fields to strings for JSON serialization
        db_entry['_id'] = str(db_entry['_id'])

        # Return the found entry
        return db_entry

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


@router.post("/data/add", tags=["MongoDB"])
async def add_data(
    token: str = Depends(oauth2_scheme),
    modified_data: Dict = Body(...)
):
    """
    Insert the modified data as a new entry in MongoDB.
    """
    current_user = verify_token(token)  # Verify the JWT token, but don't restrict by role

    try:
        # Ensure that the _id is not present in the modified data to avoid conflicts with MongoDB
        if "_id" in modified_data:
            del modified_data["_id"]  # Remove the _id field if present

        # Assign a new ObjectId to the new entry
        modified_data["_id"] = ObjectId()

        # Insert the modified entry as new data into MongoDB
        result = db.lfb.insert_one(modified_data)

        # Return the inserted data and the new ObjectId (convert ObjectId to string)
        inserted_data = object_id_to_str(modified_data)

        return {"inserted_id": str(result.inserted_id), "message": "New data added successfully", "modified_data": inserted_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inserting data: {str(e)}")