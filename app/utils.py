import os
import pymongo
import joblib
import logging
from app.features import FEATURE_COLUMNS
from dotenv import load_dotenv
import numpy as np

load_dotenv()

# Setup logging
logging.basicConfig(filename='logs/app.log', level=logging.INFO)

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "lfb"
COLLECTION_NAME = "lfb"

def connect_to_mongo():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    logging.info("Connected to MongoDB")
    return collection

def load_model_and_pca():
    model_path = os.path.join('model', 'model.pkl')
    pca_path = os.path.join('model', 'pca.pkl')

    with open(model_path, 'rb') as model_file:
        model = joblib.load(model_file)

    with open(pca_path, 'rb') as pca_file:
        pca = joblib.load(pca_file)

    logging.info("Loaded model and PCA from disk")
    return model, pca

def fetch_sample_data(collection, limit=10):
    sample_data = collection.find().limit(limit)
    logging.info(f"Fetched {limit} sample records from MongoDB")
    return list(sample_data)

def preprocess_test_data(raw_test_data, pca_model):
    features = [
        [
            item.get(feature, 0) for feature in FEATURE_COLUMNS
            if feature not in ['_id', 'ResponseTimeBinary']  # Exclude _id and target
        ]
        for item in raw_test_data
    ]
    
     # Debug: print number of features
    if len(features[0]) != 319:
        print(f"Number of features after filtering: {len(features[0])}")
    
    transformed_features = pca_model.transform(features)
    return transformed_features, features


def evaluate_model_on_test_set():
    collection = connect_to_mongo()
    raw_test_data = fetch_sample_data(collection)
    
    model, pca = load_model_and_pca()
    
    X_test, y_test = preprocess_test_data(raw_test_data, pca)
    y_test = np.array(y_test)
    if len(y_test.shape) > 1:
        y_test = y_test[:, 0] 
    
    predictions = model.predict(X_test)
    accuracy = (predictions == y_test).mean()
    log_evaluation_result(accuracy)
    return accuracy

def log_evaluation_result(accuracy):
    logging.basicConfig(filename='logs/evaluation.log', level=logging.INFO, 
                        format='%(asctime)s - %(message)s')
    logging.info(f'Model evaluation completed. Accuracy: {accuracy:.4f}')

def log_info(message):
    logging.info(message)


