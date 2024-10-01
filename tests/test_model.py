'''
from app.utils import connect_to_mongo, fetch_sample_data, load_model_and_pca, preprocess_test_data
from app.features import FEATURE_COLUMNS

def test_model_prediction():
    collection = connect_to_mongo()
    raw_features = fetch_sample_data(collection)

    model, pca = load_model_and_pca()
    transformed_features, _ = preprocess_test_data(raw_features, pca)
    result = model.predict(transformed_features)

    assert len(result) == len(transformed_features)
    assert all(pred >= 0 for pred in result)  
'''