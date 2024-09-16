from fastapi import FastAPI
import joblib
import logging
from app.routes import prediction, evaluation, database, token_generator  

app = FastAPI()

# logs
logging.basicConfig(filename='logs/app.log', level=logging.INFO)

# load trained model
with open('model/model.pkl', 'rb') as f:
    model = joblib.load(f)

# routes
app.include_router(prediction.router)
app.include_router(evaluation.router)
app.include_router(database.router)
app.include_router(token_generator.router)
