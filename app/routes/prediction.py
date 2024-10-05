from app.utils import load_model_and_pca, connect_to_mongo, fetch_sample_data
from fastapi import APIRouter, Depends, HTTPException, Body
from app.auth import verify_token
from bson import ObjectId
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Secret key and algorithm for JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Load the model and PCA
model, pca = load_model_and_pca()

# Path to the sample JSON file
SAMPLE_JSON_PATH = os.path.join("data", "sample_predict_data.json")

# Hilfsfunktion zum Abrufen und Transformieren von Daten
def fetch_and_transform_data():
    collection = connect_to_mongo()
    raw_features_list = fetch_sample_data(collection)

    if not raw_features_list:
        raise ValueError("Die Liste der rohen Features ist leer.")

    raw_features = raw_features_list[0]

    # Speichere den _id Wert, bevor er gelöscht wird
    document_id = raw_features.get('_id')

    # Lösche den '_id' und 'ResponseTimeBinary', wenn sie vorhanden sind
    raw_features.pop('_id', None)
    raw_features.pop('ResponseTimeBinary', None)

    # Beispiel: Entferne eine mögliche 'extra_column', falls vorhanden
    raw_features.pop("extra_column", None)

    # Transformiere die Features mit PCA
    transformed_features = pca.transform([list(raw_features.values())])

    return transformed_features, document_id

# POST-Endpoint für Vorhersagen
@router.post("/predict", tags=["Prediction"])
async def predict(token: str = Depends(oauth2_scheme)):
    # Überprüfen des Tokens und Abrufen des Benutzers
    current_user = verify_token(token)

    # Abrufen und Transformieren der Daten
    try:
        transformed_features, document_id = fetch_and_transform_data()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Modellvorhersage
    prediction = model.predict(transformed_features)

    # Konvertiere die Vorhersage in einen nativen Python-Datentyp
    predicted_value = int(prediction[0])

    # Rückgabe der Vorhersage und der Inzidenz-ID
    return {
        "predicted_response_time": predicted_value,
        "incidence_id": str(document_id)
    }

########################################
#### THIS IS ONLY FOR DEMO PURPOSES ####
########################################

# Function to load the sample data from the JSON file
def load_sample_pred_data():
    try:
        with open(SAMPLE_JSON_PATH, 'r') as f:
            sample_data = json.load(f)
        return sample_data
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Sample data file not found.")

# Load the sample data from JSON
sample_data = load_sample_pred_data()

# POST endpoint for predictions
@router.post("/predict_test", tags=["Prediction"])
async def predict(
    token: str = Depends(oauth2_scheme), 
    modified_data: dict = Body(sample_data)  # Preload the sample JSON data as the default request body
):
    # Verify the token
    current_user = verify_token(token)

    # Allow modifications by updating the sample data with the input request body
    sample_data.update(modified_data)

    # Transform the features using PCA
    transformed_features = pca.transform([list(sample_data.values())])

    # Make a prediction using the model
    prediction = model.predict(transformed_features)
    predicted_value = int(prediction[0])

    # Insert the predicted value back into the data
    sample_data['ResponseTimeBinary'] = predicted_value

    # Insert the modified data into MongoDB and get the new ObjectId
    collection = connect_to_mongo()
    result = collection.insert_one(sample_data)

    # Return the prediction and the new MongoDB ObjectId
    return {
        "predicted_response_time": predicted_value,
        "inserted_id": str(result.inserted_id),
        "message": "New data with prediction added successfully"
    }