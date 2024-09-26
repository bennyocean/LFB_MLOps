from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pymongo import MongoClient
from passlib.context import CryptContext
from dotenv import load_dotenv
import jwt 
from jwt import PyJWTError 
from pydantic import BaseModel
import os

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Hole den MONGO_URI aus der Umgebungsvariablen
MONGO_URI = os.getenv("MONGO_URI")

# Verbindung zu MongoDB herstellen mit MONGO_URI
client = MongoClient(MONGO_URI)
db = client["lfb"]  # Wähle die Datenbank, in deinem Fall "lfb"
users_collection = db["users"]

# Password Hashing Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Setup
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# APIRouter erstellen
router = APIRouter()

# OAuth2 Schema für Bearer Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Passwort hashen
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Benutzer in die Datenbank einfügen
def create_user_in_db(username: str, password: str, role: str):
    if role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role. Only 'user' or 'admin' roles are allowed.")


    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    user = {
        "username": username,
        "hashed_password": hash_password(password),
        "role": role
    }

    result = users_collection.insert_one(user)  # Benutzer einfügen

# Definiere ein Pydantic-Modell für den Request-Body
class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: str

# Token Überprüfung und Rollenvalidierung
def get_current_admin_user(token: str = Depends(oauth2_scheme)):
    try:
        # JWT-Token dekodieren
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        if role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can perform this action")
        return {"username": username, "role": role}
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Admin-geschützter Endpoint für das Erstellen von Benutzern
@router.post("/create_user")
def create_user(user: UserCreateRequest, current_admin: dict = Depends(get_current_admin_user)):
    # Nur Admins dürfen diesen Endpoint verwenden
    create_user_in_db(user.username, user.password, user.role)
    return {"message": f"User {user.username} with role {user.role} created successfully."}