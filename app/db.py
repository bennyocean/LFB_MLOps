from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId

# Helper function to convert MongoDB ObjectId to string
def object_id_to_str(doc):
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

db = client.lfb  
collection = db.lfb  
