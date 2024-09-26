from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from passlib.context import CryptContext
from dotenv import load_dotenv
import jwt
import os

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()

# MongoDB Setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["lfb"]  # Wähle die Datenbank
users_collection = db["users"]

# Password Hashing Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Setup
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

router = APIRouter()

# Pydantic Modell für die Anmeldeinformationen
class LoginRequest(BaseModel):
    username: str
    password: str

# Benutzer aus der Datenbank holen
def get_user_from_db(username: str):
    return users_collection.find_one({"username": username})

# Passwort verifizieren
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Token erstellen
def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

# Token-Generierungs-Endpoint mit Benutzeranmeldung (JSON basierend)
@router.post("/generate-token")
def generate_token(login_request: LoginRequest):
    # Benutzer in der Datenbank finden
    user = get_user_from_db(login_request.username)
    
    # Wenn der Benutzer nicht existiert oder das Passwort nicht korrekt ist
    if not user or not verify_password(login_request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Token-Payload mit Benutzername und Rolle erstellen
    payload = {
        "sub": user["username"],
        "role": user["role"]
    }

    # Token erstellen
    token = create_access_token(payload)

    return {"token": token}
