from app.utils import load_model_and_pca, connect_to_mongo, fetch_sample_data
from fastapi import APIRouter, Depends, HTTPException
from app.auth import verify_token
from app.db import db
from bson import ObjectId
from dotenv import load_dotenv
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# Load environment variables
load_dotenv()

# Secret key and algorithm for JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Lade das Modell und PCA einmalig
model, pca = load_model_and_pca()

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
