from pymongo import MongoClient
from app.auth import hash_password 

MONGODB_URL = "mongodb+srv://admin:R0vTrwRkhguP0tK4@lfb.2ilrk.mongodb.net/lfb?retryWrites=true&w=majority"

client = MongoClient(MONGODB_URL)
db = client.lfb
collection = db.users

# Create a new user and admin
new_users = [{
        "username": "admin",
        "hashed_password": hash_password("password"),
        "role": "admin"},
        {"username": "user",
        "hashed_password": hash_password("password"),
        "role": "user"
}]

# Insert the new users into the collection
insert_result = collection.insert_many(new_users)
print(f"New users created with ids: {insert_result.inserted_ids}")