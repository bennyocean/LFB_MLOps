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
    # Login as a regular user to get the token
    token_response = client.post("/token", data={"username": user_username, "password": user_password})
    assert token_response.status_code == 200, f"Error: {token_response.json()}"
    access_token = token_response.json()["access_token"]

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
    # Login as a regular user to get the token
    token_response = client.post("/token", data={"username": user_username, "password": user_password})
    assert token_response.status_code == 200, f"Error: {token_response.json()}"
    access_token = token_response.json()["access_token"]

    # Add a new data entry (assuming the add endpoint is "/data/add-sample")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/data/add", headers=headers)

    # Debugging: Log response
    print(f"Add Data Entry Response: {response.json()}")

    # Ensure that the data was added successfully
    assert response.status_code == 200, f"Error: {response.json()}"
    assert "inserted_ids" in response.json(), "Data insertion failed"
    inserted_ids = response.json()["inserted_ids"]
    assert len(inserted_ids) > 0, "No entries were added"

    # Adding delay to allow MongoDB to propagate the change
    sleep(1)  # Optional: Increase if needed

    # Verify that the entry was added directly in MongoDB
    sample_id = inserted_ids[0]
    print(f"Sample ID inserted: {sample_id}")
    
    object_id = bson.ObjectId(sample_id)
    db_entry = db.lfb.find_one({"_id": object_id})
    assert db_entry is not None, "Data was not inserted into MongoDB"
    print(f"Data in MongoDB: {db_entry}")

    # Verify the entry was added by fetching one of the inserted ids using the API
    verify_response = client.get(f"/data/{sample_id}", headers=headers)
    assert verify_response.status_code == 200, f"Error: {verify_response.json()}"
    print(f"Verified Inserted Data via API: {verify_response.json()}")



