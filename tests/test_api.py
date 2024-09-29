import math
from fastapi.testclient import TestClient
from app.main import app
import jwt
from datetime import datetime, timedelta
import os
from app.utils import evaluate_model_on_test_set
from unittest.mock import patch

client = TestClient(app)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# Helper function to create a JWT token for testing
def create_test_token(role="admin"):
    expiration = datetime.now() + timedelta(hours=1)  
    token = jwt.encode({"sub": "test_user", "role": role, "exp": expiration}, SECRET_KEY, ALGORITHM)
    return token

# Helper function to preprocess input data for testing (not needed for this specific test)
def preprocess_input(incident_time, distance_to_station):
    hour = int(incident_time.split(":")[0])  
    hour_sin, hour_cos = encode_time(hour)  
    distance_log_value = math.log(distance_to_station)  
    
    return {
        "IsBankholiday": 0,  
        "IsWeekend": 1,      
        "DistanceStationLog": distance_log_value,
        "Hour_sin": hour_sin,
        "Hour_cos": hour_cos,
        "Weekday_sin": 0.5,  
        "Weekday_cos": 0.866025,  
        "Month_sin": 0.5, 
        "Month_cos": 0.866025  
    }

def encode_time(hour):
    max_hour = 24
    hour_sin = math.sin(2 * math.pi * hour / max_hour)
    hour_cos = math.cos(2 * math.pi * hour / max_hour)
    return hour_sin, hour_cos

### Unit Test for Prediction Endpoint

def test_prediction_endpoint_success():
    # Create an admin token
    token = create_test_token(role="admin")
    
    # Send POST request to /predict with a valid token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/predict", headers=headers)

    # Ensure the response status code is 200 (Success)
    assert response.status_code == 200

    # Ensure the predicted response time and incidence ID are in the response
    json_response = response.json()
    assert "predicted_response_time" in json_response
    assert "incidence_id" in json_response

def test_prediction_endpoint_for_user():
    # Create a user token
    token = create_test_token(role="user")
    
    # Send POST request to /predict with a valid user token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/predict", headers=headers)

    # Ensure the response status code is 200 (Success)
    assert response.status_code == 200
    json_response = response.json()
    assert "predicted_response_time" in json_response
    assert "incidence_id" in json_response

def test_prediction_endpoint_invalid_token():
    # Verwende einen ungültigen Token
    invalid_token = "thisisnotavalidtoken"

    # Sende die POST-Anfrage an /predict mit einem ungültigen Token
    headers = {"Authorization": f"Bearer {invalid_token}"}
    response = client.post("/predict", headers=headers)

    # Überprüfen, ob der Statuscode 401 Unauthorized ist
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

### Unit Test for Evaluation Endpoint

def test_evaluate_endpoint_success():
    # Create an admin token
    token = create_test_token(role="admin")

    # Send POST request to /evaluate with a valid token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/evaluate", headers=headers)

    # Ensure the response status code is 200 (Success)
    assert response.status_code == 200

    # Ensure the evaluation result contains accuracy
    json_response = response.json()
    assert "evaluation_result" in json_response
    assert "accuracy" in json_response["evaluation_result"]

def test_evaluate_endpoint_for_user():
    # Create a user token
    token = create_test_token(role="user")

    # Send POST request to /evaluate with a valid user token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/evaluate", headers=headers)

    # Ensure the response status code is 200 (Success)
    assert response.status_code == 200
    json_response = response.json()
    assert "evaluation_result" in json_response
    assert "accuracy" in json_response["evaluation_result"]

def test_evaluate_endpoint_invalid_token():
    # Verwende einen ungültigen Token
    invalid_token = "thisisnotavalidtoken"

    # Sende die POST-Anfrage an /evaluate mit einem ungültigen Token
    headers = {"Authorization": f"Bearer {invalid_token}"}
    response = client.post("/evaluate", headers=headers)

    # Überprüfen, ob der Statuscode 401 Unauthorized ist
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
