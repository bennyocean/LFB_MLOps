from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Hole den MONGO_URI aus der Umgebungsvariable
MONGO_URI = os.getenv("MONGO_URI")

# Verbindung zu MongoDB herstellen mit MONGO_URI
client = MongoClient(MONGO_URI)
db = client["lfb"]  # Wähle die Datenbank, in deinem Fall "lfb"
users_collection = db["users"]

# APIRouter erstellen
router = APIRouter()

# Neuer Endpunkt, um alle Benutzer anzuzeigen (ohne Passwort)
@router.get("/users")
def get_users():
    users = users_collection.find({}, {"_id": 0, "username": 1, "role": 1}) 
    
    # Konvertiere die Benutzer aus MongoDB in eine Liste
    user_list = [{"username": user["username"], "role": user["role"]} for user in users]
    
    return {"users": user_list}