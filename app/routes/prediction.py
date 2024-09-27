from app.utils import load_model_and_pca, connect_to_mongo, fetch_sample_data
from fastapi import APIRouter, Depends
from app.auth import verify_token

router = APIRouter()

model, pca = load_model_and_pca()

def fetch_and_transform_data():
    collection = connect_to_mongo()
    raw_features_list = fetch_sample_data(collection)

    for raw_features in raw_features_list:
        if '_id' in raw_features:
            del raw_features['_id']

    first_raw_features = raw_features_list[0]

    if "extra_column" in first_raw_features:
        del first_raw_features["extra_column"]

    transformed_features = pca.transform([list(first_raw_features.values())])

    return transformed_features



@router.post("/predict", tags=["Model Prediction"])
def predict(token: str = Depends(verify_token)):
    transformed_features = fetch_and_transform_data()

    prediction = model.predict(transformed_features)
    return {"predicted_response_time": prediction[0]}
