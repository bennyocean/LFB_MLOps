from app.utils import load_model_and_pca, preprocess_test_data, connect_to_mongo, fetch_sample_data
from fastapi import APIRouter, Depends
from app.auth import verify_token

router = APIRouter()

model, pca = load_model_and_pca()

def fetch_and_transform_data():
    collection = connect_to_mongo()
    raw_features = fetch_sample_data(collection)

    # Exclude '_id' from raw features
    del raw_features['_id']

    # Preprocess the test data with PCA
    transformed_features, _ = preprocess_test_data(raw_features, pca)
    return transformed_features

@router.post("/predict")
def predict(token: str = Depends(verify_token)):
    # Fetch and transform the input data
    transformed_features = fetch_and_transform_data()

    prediction = model.predict(transformed_features)
    return {"predicted_response_time": prediction[0]}
