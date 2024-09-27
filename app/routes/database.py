from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from app.db import db
from app.auth import verify_token
import random

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Helper function to convert MongoDB document ObjectId to string
def object_id_to_str(doc):
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

# Endpoint to read data from lfb.lfb with authorization (no role restriction)
@router.get("/data", tags=["MongoDB"])
async def read_data(token: str = Depends(oauth2_scheme)):
    current_user = verify_token(token)  # Verify the JWT token, but don't restrict by role

    try:
        data = list(db.lfb.find().limit(15))  # Read 15 documents for now
        if not data:
            raise HTTPException(status_code=404, detail="No data found in lfb.lfb")
        
        # Convert ObjectId to string for each document
        data = [object_id_to_str(doc) for doc in data]
        
        return {"data": data}
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

# Endpoint to add new data by simulating 5 samples with authorization (no role restriction)
@router.post("/data/add", tags=["MongoDB"])
async def add_data(token: str = Depends(oauth2_scheme)):
    current_user = verify_token(token)  # Verify the JWT token, but don't restrict by role

    try:
        # Sample 5 random entries from the lfb.lfb collection
        all_entries = list(db.lfb.find())
        sampled_entries = random.sample(all_entries, 5)

        # Create new ObjectIds for the sampled entries to avoid duplicates
        for entry in sampled_entries:
            entry['_id'] = ObjectId()  # Assign a new ObjectId to each entry

        # Insert the sampled entries as new data
        result = db.lfb.insert_many(sampled_entries)

        # Convert ObjectId to string for each inserted document
        inserted_ids = [str(id_) for id_ in result.inserted_ids]

        return {"inserted_ids": inserted_ids, "message": "Sampled data added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sampling or inserting data: {str(e)}")