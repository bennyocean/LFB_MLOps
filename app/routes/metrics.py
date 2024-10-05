from fastapi import APIRouter
from starlette.responses import PlainTextResponse
from prometheus_client import generate_latest

router = APIRouter()

metrics = generate_latest()

@router.get("/metrics", tags=["Monitoring"])
async def custom_metrics():
    
    from prometheus_client import generate_latest
    metrics = generate_latest()
    return PlainTextResponse(metrics)