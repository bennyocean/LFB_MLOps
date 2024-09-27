from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from airflow.providers.mongo.hooks.mongo import MongoHook
from datetime import datetime, timedelta
import joblib
from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA  
from app.features import FEATURE_COLUMNS 

# Load environment variables
load_dotenv()
mongo_conn_uri = os.getenv('MONGO_URI')

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2023, 9, 25),
}

# Define DAG
with DAG('predict_model_dag',
         default_args=default_args,
         schedule='@daily',
         catchup=False) as dag:

    # Test MongoDB connection
    def test_mongo_connection():
        try:
            connection = BaseHook.get_connection('mongo_conn')
            print(f"Connection URI: {connection.get_uri()}")
            print("MongoDB connection works correctly.")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")

    # Task to load the model and PCA
    def load_model(ti):
        dag_file_directory = os.path.dirname(os.path.realpath(__file__))
        model_path = os.path.join(dag_file_directory, '../../model/model.pkl')
        pca_path = os.path.join(dag_file_directory, '../../model/pca.pkl')

        model = joblib.load(model_path)
        pca = joblib.load(pca_path)

        ti.xcom_push(key='model', value='Model loaded')

    # Task to fetch data from MongoDB
    def fetch_data_from_mongodb():
        mongo_hook = MongoHook(conn_id='mongo_conn')
        client = mongo_hook.get_conn()

        db = client['lfb']
        collection = db['lfb']

        data = pd.DataFrame(list(collection.find()))
        return data

    # Task to preprocess the data
    def preprocess_data(data, pca):
        if '_id' in data.columns:
            data = data.drop('_id', axis=1)
        if 'ResponseTimeBinary' in data.columns:
            data = data.drop('ResponseTimeBinary', axis=1)

        data = data[FEATURE_COLUMNS]

        transformed_data = pca.transform(data) if pca else data
        return transformed_data

    # Task to make predictions
    def make_predictions(ti):
        model, pca = ti.xcom_pull(task_ids='load_model_task')
        raw_data = ti.xcom_pull(task_ids='fetch_data_task')

        processed_data = preprocess_data(raw_data, pca)
        predictions = model.predict(processed_data)
        return predictions

    # Task to store predictions in MongoDB
    def store_predictions_in_mongodb(ti):
        mongo_hook = MongoHook(conn_id=None, conn_uri=mongo_conn_uri)
        client = mongo_hook.get_conn()

        db = client['lfb']
        collection = db['predictions']

        predictions = ti.xcom_pull(task_ids='make_predictions_task')
        prediction_docs = [{"prediction": pred, "timestamp": datetime.now()} for pred in predictions]
        collection.insert_many(prediction_docs)

        print(f"Inserted {len(prediction_docs)} predictions into MongoDB.")

    # Define tasks
    test_mongo_conn_task = PythonOperator(
        task_id='test_mongo_conn_task',
        python_callable=test_mongo_connection
    )

    load_model_task = PythonOperator(
        task_id='load_model_task',
        python_callable=load_model
    )

    fetch_data_task = PythonOperator(
        task_id='fetch_data_task',
        python_callable=fetch_data_from_mongodb
    )

    make_predictions_task = PythonOperator(
        task_id='make_predictions_task',
        python_callable=make_predictions
    )

    store_predictions_task = PythonOperator(
        task_id='store_predictions_task',
        python_callable=store_predictions_in_mongodb
    )

    # Set task dependencies
    test_mongo_conn_task >> load_model_task >> fetch_data_task >> make_predictions_task >> store_predictions_task
