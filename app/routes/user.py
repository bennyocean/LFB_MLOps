from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.auth import create_access_token, verify_password, hash_password, verify_token
from app.models import User
from app.db import db
from bson import ObjectId
from jose import jwt, JWTError
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Secret key and algorithm for JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/token", tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.users.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):  # Verify 'hashed_password'
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/users", response_model=User, tags=["User Management"])
async def create_user(user: User, token: str = Depends(oauth2_scheme)):
    current_user = verify_token(token)

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Operation not permitted")

    user.hashed_password = hash_password(user.hashed_password)  # Hash the password and store as 'hashed_password'
    user.role = "user"  # Default role
    result = db.users.insert_one(user.model_dump(exclude={"id"}))  # Use model_dump to exclude 'id'
    user.id = str(result.inserted_id)
    return user

@router.get("/users/{user_id}", response_model=User, tags=["User Management"])
async def read_user(user_id: str, token: str = Depends(oauth2_scheme)):
    current_user = verify_token(token)

    user = db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user["role"] != "admin" and current_user["username"] != user["username"]:
        raise HTTPException(status_code=403, detail="Operation not permitted")

    return User(**user)

@router.put("/users/{user_id}", response_model=User, tags=["User Management"])
async def update_user(user_id: str, user: User, token: str = Depends(oauth2_scheme)):
    current_user = verify_token(token)

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Operation not permitted")

    result = db.users.update_one({"_id": ObjectId(user_id)}, {"$set": user.model_dump(exclude={"id"})})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found or no changes made")
    return user

@router.delete("/users/{user_id}", tags=["User Management"])
async def delete_user(user_id: str, token: str = Depends(oauth2_scheme)):
    current_user = verify_token(token)

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Operation not permitted")

    result = db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted successfully"}

@router.get("/users", response_model=list[User], tags=["User Management"])
async def get_users(token: str = Depends(oauth2_scheme)):
    try:
        # Decode the token and extract claims
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")

        if username is None or role is None:
            raise HTTPException(status_code=401, detail="Token payload is missing 'sub' or 'role'")
        
        # Ensure the role is admin
        if role != "admin":
            raise HTTPException(status_code=403, detail="Operation not permitted: Admins only")
        
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")
    
    # Fetch users if token is valid and the user is an admin
    users = list(db.users.find())
    # Handle missing passwords with a default value
    return [User(**{**user, "hashed_password": user.get("hashed_password", "")}) for user in users]
