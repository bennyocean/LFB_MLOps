import pytest
from fastapi.testclient import TestClient
from time import sleep
from app.main import app
from app.db import db
import bson
from time import sleep

client = TestClient(app)

# User credentials (for non-admin tests)
user_username = "user"
user_password = "password"

token_response = client.post("/token", data={"username": user_username, "password": user_password})
assert token_response.status_code == 200, f"Error: {token_response.json()}"
access_token = token_response.json()["access_token"]

# Setup for MongoDB ping and logging collections
@pytest.fixture
def setup_mongodb():
    # Ensure MongoDB is reachable and collections exist
    db_stats = db.command("dbstats")
    print(f"MongoDB Stats: {db_stats}")
    yield

# Test 1: Ping MongoDB (without any credentials)
def test_ping_mongodb(setup_mongodb):
    # Check if MongoDB is reachable by executing a basic command
    try:
        server_info = db.command("ping")
        print(f"MongoDB Ping: {server_info}")
        assert server_info["ok"] == 1
    except Exception as e:
        pytest.fail(f"MongoDB Ping failed: {str(e)}")

# Test 2: Log the collection names in MongoDB (without any credentials)
def test_log_collection_names(setup_mongodb):
    try:
        collections = db.list_collection_names()
        print(f"MongoDB Collections: {collections}")
        assert len(collections) > 0, "No collections found in MongoDB"
    except Exception as e:
        pytest.fail(f"Failed to retrieve collections: {str(e)}")

# Test 3: Read one data entry from a collection (with user credentials)
def test_read_one_data_entry():
    # Fetch entry from the lfb collection
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/data", headers=headers)  # Assuming the read endpoint is "/data/one"

    # Debugging: Log response
    print(f"Read Data Entry Response: {response.json()}")

    # Ensure that a valid entry is returned
    assert response.status_code == 200, f"Error: {response.json()}"
    assert len(response.json()) > 0, "No data entries returned"

# Test 4: Add new data entry and verify addition (with user credentials)
def test_add_new_data_entry():
    # Fetch a sample entry from the lfb collection (assuming the endpoint returns a list)
    headers = {"Authorization": f"Bearer {access_token}"}
    fetch_response = client.get("/data", headers=headers)  # Assuming the read endpoint is "/data"
    
    # Debugging: Log fetch response
    print(f"Fetched Data Entries Response: {fetch_response.json()}")
    
    # Ensure the response contains at least one entry
    assert fetch_response.status_code == 200, f"Error: {fetch_response.json()}"
    fetched_entries = fetch_response.json()
    assert len(fetched_entries) > 0, "No data entries returned"
    
    # Take the first entry from the list and remove '_id'
    new_data_entry = fetched_entries[0]
    new_data_entry.pop('_id', None)  # Remove the _id to simulate new data insertion
    
    # Debugging: Log modified data entry
    print(f"New Data Entry (without _id): {new_data_entry}")

    # Add the new data entry to the database via the /data/add endpoint
    add_response = client.post("/data/add", headers=headers, json=new_data_entry)

    # Debugging: Log response from adding new data
    print(f"Add Data Entry Response: {add_response.json()}")

    # Ensure that the data was added successfully
    assert add_response.status_code == 200, f"Error: {add_response.json()}"
    assert "inserted_id" in add_response.json(), "Data insertion failed"
    inserted_id = add_response.json()["inserted_id"]
    assert len(inserted_id) > 0, "No entries were added"

    # Verify that the entry was added directly in MongoDB
    print(f"Sample ID inserted: {inserted_id}")
    
    object_id = bson.ObjectId(inserted_id)
    db_entry = db.lfb.find_one({"_id": object_id})
    assert db_entry is not None, "Data was not inserted into MongoDB"
    print(f"Data in MongoDB: {db_entry}")

    # Verify the entry was added by fetching one of the inserted ids using the API
    verify_response = client.get(f"/data/{inserted_id}", headers=headers)
    assert verify_response.status_code == 200, f"Error: {verify_response.json()}"
    print(f"Verified Inserted Data via API: {verify_response.json()}")