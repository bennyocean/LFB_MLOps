import pytest
from fastapi.testclient import TestClient
from time import sleep
from app.main import app
from app.db import db
from app.auth import hash_password 

client = TestClient(app)

# Admin user credentials
admin_username = "admin"
admin_password = "password"

# Setup test user data
@pytest.fixture
def setup_test_db():
    # Hash the password for testuser_pytest
    test_user = {
        "username": "testuser_pytest",
        "hashed_password": hash_password("hashedpassword"),  # Properly hash the password
        "role": "user"
    }
    if not db.users.find_one({"username": "testuser_pytest"}):
        print("Inserting testuser_pytest into MongoDB with hashed password")
        db.users.insert_one(test_user)
    else:
        print("Test user 'testuser_pytest' already exists in MongoDB")
    yield
    # Do not delete any users after tests


# Test for token generation (POST /token) and print the token
def test_token_generation(setup_test_db):
    response = client.post("/token", data={"username": admin_username, "password": admin_password})
    assert response.status_code == 200, f"Error: {response.json()}"
    token = response.json()["access_token"]
    print(f"Generated Token: {token}")
    assert "access_token" in response.json()

# Login as admin to get token
token_response = client.post("/token", data={"username": admin_username, "password": admin_password})
access_token = token_response.json()["access_token"]

# Test for creating a user (POST /users)
def test_create_user(setup_test_db):
    # Create a new user (hashed_password is required by the schema, role must also be provided)
    new_user = {
        "username": "testuser_pytest_2",
        "hashed_password": "testpassword",  # Pass the plain password; the API will hash it
        "role": "user"  # Include the role as required by the User schema
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/users", json=new_user, headers=headers)

    # Debugging: Log response
    print(f"Create User Response: {response.json()}")

    # Check if the user was created successfully
    assert response.status_code == 200, f"Error: {response.json()}"
    assert response.json()["username"] == new_user["username"]


# Test for getting users (GET /users)
def test_get_users(setup_test_db):
    # Get the list of users
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/users", headers=headers)

    # Debugging: Log response
    print(f"Get Users Response: {response.json()}")

    assert response.status_code == 200, f"Error: {response.json()}"
    assert len(response.json()) > 0

# Test for reading a specific user (GET /users/{user_id})
def test_read_user(setup_test_db):
    # Retry fetching the user a few times if it's not found immediately
    retries = 3
    for _ in range(retries):
        test_user = db.users.find_one({"username": "testuser_pytest"})
        if test_user:
            print(f"Found testuser_pytest in MongoDB: {test_user}")
            break
        print("Retrying to find testuser_pytest in MongoDB...")
        sleep(1)
    else:
        pytest.fail("Test user 'testuser_pytest' not found in the database")

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"/users/{test_user['_id']}", headers=headers)

    # Debugging: Log response
    print(f"Read User Response: {response.json()}")

    assert response.status_code == 200, f"Error: {response.json()}"
    assert response.json()["username"] == "testuser_pytest"

# Test for updating a user (PUT /users/{user_id})
def test_update_user(setup_test_db):
    # Fetch the user first
    test_user = db.users.find_one({"username": "testuser_pytest"})
    if not test_user:
        pytest.fail("Test user 'testuser_pytest' not found in the database before update")

    # Debugging: Log user details before the update
    print(f"Test User before update: {test_user}")

    # Update the user
    updated_data = {
        "username": "user_pytest_updated",
        "hashed_password": "newpassword",  # Pass plain password; API will handle hashing
        "role": "user"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.put(f"/users/{test_user['_id']}", json=updated_data, headers=headers)

    # Debugging: Log response
    print(f"Update User Response: {response.json()}")

    # Re-fetch the user to confirm the update
    updated_user = db.users.find_one({"username": "user_pytest_updated"})
    print(f"Updated User in DB: {updated_user}")

    assert response.status_code == 200, f"Error: {response.json()}"
    assert response.json()["username"] == "user_pytest_updated"
    assert updated_user is not None, "User was not updated in the database"


# Test for deleting a user (DELETE /users/{user_id})
def test_delete_user(setup_test_db):
    # Fetch the updated user first (we will first check if the update happened correctly)
    print("Fetching updated user before deletion...")
    test_user = db.users.find_one({"username": "user_pytest_updated"})
    if not test_user:
        # Add a retry mechanism in case the update wasn't completed in time
        retries = 3
        for _ in range(retries):
            test_user = db.users.find_one({"username": "user_pytest_updated"})
            if test_user:
                print(f"Found user_pytest_updated in MongoDB: {test_user}")
                break
            print("Retrying to find user_pytest_updated in MongoDB...")
            sleep(1)
        else:
            pytest.fail("Test user 'user_pytest_updated' not found in the database")

    # If found, proceed to delete
    print(f"Test User ready for deletion: {test_user}")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.delete(f"/users/{test_user['_id']}", headers=headers)

    # Debugging: Log response
    print(f"Delete User Response: {response.json()}")

    assert response.status_code == 200, f"Error: {response.json()}"
    assert response.json()["detail"] == "User deleted successfully"

