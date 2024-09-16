import math
from fastapi.testclient import TestClient
from app.main import app
import jwt
from datetime import datetime, timedelta
import os

client = TestClient(app)

SECRET_KEY = os.getenv("SECRET_KEY")

# Helper function to create a JWT token for testing
def create_test_token():
    expiration = datetime.now() + timedelta(hours=1)  
    token = jwt.encode({"user_id": 1, "exp": expiration}, SECRET_KEY, algorithm="HS256")
    return token

def encode_time(hour):
    max_hour = 24
    hour_sin = math.sin(2 * math.pi * hour / max_hour)
    hour_cos = math.cos(2 * math.pi * hour / max_hour)
    return hour_sin, hour_cos

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

def test_predict_endpoint():
    input_data = preprocess_input("12:00", 5.0)
    headers = {"Authorization": f"Bearer {create_test_token()}"}

    response = client.post("/predict", json=input_data, headers=headers)
    
    print(response.json())

    assert response.status_code == 200
    assert "predicted_response_time" in response.json()


def test_evaluate_endpoint():
    headers = {"Authorization": f"Bearer {create_test_token()}"}
    response = client.get("/evaluate", headers=headers)
    
    print(response.json())

    assert response.status_code == 200
    assert "model_accuracy" in response.json()
