from fastapi import FastAPI
import joblib
import logging
from app.routes import prediction, evaluation, database, user, metrics
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Instrumentator for Prometheus metrics
instrumentator = Instrumentator().instrument(app)

# logs
eval_handler = logging.FileHandler('logs/evaluation.log')
eval_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
eval_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(eval_handler)

# load trained model
with open('model/model.pkl', 'rb') as f:
    model = joblib.load(f)

# routes
app.include_router(user.router)
app.include_router(database.router)
app.include_router(prediction.router)
app.include_router(evaluation.router)
app.include_router(metrics.router)