from pydantic import BaseModel

class IncidentData(BaseModel):
    incident_time: str
    grid_node: int

class NewData(BaseModel):
    incident_time: str
    grid_node: int
