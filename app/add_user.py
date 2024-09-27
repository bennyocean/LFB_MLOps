from pymongo import MongoClient
from app.auth import hash_password 

# Replace with your MongoDB connection string
MONGODB_URL = "mongodb+srv://admin:R0vTrwRkhguP0tK4@lfb.2ilrk.mongodb.net/lfb?retryWrites=true&w=majority"

# Connect to the MongoDB database
client = MongoClient(MONGODB_URL)

# Select the database and collection
db = client.lfb
collection = db.users

# Create a new user and admin with admin rights
new_users = [{
        "username": "user",
        "hashed_password": hash_password("password"),  # Hash the password for security
        "role": "user"},
        {"username": "user",
        "hashed_password": hash_password("password"),  # Hash the password for security
        "role": "user"
}]

# Insert the new users into the collection
insert_result = collection.insert_many(new_users)
print(f"New users created with ids: {insert_result.inserted_ids}")