from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional

class User(BaseModel):
    id: str = Field(default_factory=str)
    username: str
    hashed_password: Optional[str]
    role: str

    class Config:
        json_encoders = {ObjectId: str}


class IncidentData(BaseModel):
    incident_time: str
    grid_node: int

    class Config:
        json_encoders = {ObjectId: str}

class NewData(BaseModel):
    incident_time: str
    grid_node: int

    class Config:
        json_encoders = {ObjectId: str}
