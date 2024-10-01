from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)

db = client["lfb"]
users_collection = db["users"]