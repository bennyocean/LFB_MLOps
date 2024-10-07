from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime, timedelta
from pymongo import MongoClient
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
from sklearn.decomposition import PCA
from imblearn.under_sampling import RandomUnderSampler
import joblib
import pandas as pd
import logging

default_args = {
    'owner': 'airflow',
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2023, 9, 25),
}

def store_model_metrics(ti):
    connection = BaseHook.get_connection('mongo_conn')
    mongo_uri = connection.get_uri()

    client = MongoClient(mongo_uri)
    db_name = 'lfb'
    collection_name = 'lfb'
    db = client[db_name]
    collection = db[collection_name]

    test_data = pd.DataFrame(list(collection.find()))
    test_data = test_data.drop(columns=['_id'], errors='ignore')

    if 'data' in test_data.columns:
        test_data = test_data.drop(columns=['data'])
        logging.info("'data' column dropped.")

    X_test = test_data.drop(columns=['ResponseTimeBinary'], errors='ignore')
    y_test = test_data['ResponseTimeBinary']

    missing_X = X_test.isna().sum()
    missing_y = y_test.isna().sum()
    logging.info(f"Missing values (X_test): \n{missing_X[missing_X > 0]}")
    logging.info(f"Missing values (y_test): {missing_y}")

    combined = pd.concat([X_test, y_test], axis=1)
    combined_cleaned = combined.dropna()

    X_cleaned = combined_cleaned.drop(columns=['ResponseTimeBinary'])
    y_cleaned = combined_cleaned['ResponseTimeBinary']

    if X_cleaned.empty or y_cleaned.empty:
        raise ValueError("No valid samples left after removing rows with NaN values.")

    rUs = RandomUnderSampler(random_state=666)
    X_resampled, y_resampled = rUs.fit_resample(X_cleaned, y_cleaned)

    pca = PCA(n_components=0.85)
    X_resampled_pca = pca.fit_transform(X_resampled)

    model_path = "/opt/airflow/model/model.pkl" 
    current_model = joblib.load(model_path)
    
    y_pred = current_model.predict(X_resampled_pca)
    precision = precision_score(y_resampled, y_pred)
    recall = recall_score(y_resampled, y_pred)
    f1 = f1_score(y_resampled, y_pred)
    accuracy = accuracy_score(y_resampled, y_pred)

    metrics = {
        "model_name": "voting_classifier_hard",
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "accuracy": accuracy,
        "calculated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    metrics_db_name = 'lfb'
    metrics_collection_name = 'model_metrics_collection'
    metrics_db = client[metrics_db_name]
    metrics_collection = metrics_db[metrics_collection_name]
    metrics_collection.insert_one(metrics)
    print(f"Model metrics stored successfully in MongoDB.")



with DAG('evaluate_model_performance_dag',
         default_args=default_args,
         schedule_interval=None,  
         catchup=False) as dag:

    store_metrics_task = PythonOperator(
        task_id='store_metrics',
        python_callable=store_model_metrics
    )

    store_metrics_task
