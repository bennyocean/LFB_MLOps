from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime, timedelta
import joblib
import os
import pandas as pd
import numpy as np
from app.features import FEATURE_COLUMNS
from dotenv import load_dotenv
import logging
import sys
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Set default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2023, 9, 25),
}

# Define the DAG
with DAG('predict_model_dag',
         default_args=default_args,
         schedule='@daily',
         catchup=False) as dag:
    
    # Load model and PCA task
    def load_model(ti):
        model_path = "/opt/airflow/model/model.pkl"
        pca_path = "/opt/airflow/model/pca.pkl"

        ti.xcom_push(key='model_path', value=model_path)
        ti.xcom_push(key='pca_path', value=pca_path)


    load_model_task = PythonOperator(
        task_id='load_model_task',
        python_callable=load_model
    )

    def fetch_data_from_mongodb():
        try:
            connection = BaseHook.get_connection('mongo_conn')  
            mongo_uri = connection.get_uri()  

            if not mongo_uri:
                raise ValueError("MongoDB URI not found in Airflow connection.")

            print(f"MongoDB URI: {mongo_uri}")

            client = MongoClient(mongo_uri)
            db = client['lfb']
            collection = db['lfb']
            data = pd.DataFrame(list(collection.find()))
            return data

        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    fetch_data_task = PythonOperator(
        task_id='fetch_data_task',
        python_callable=fetch_data_from_mongodb
    )

    # Preprocess data task
    def preprocess_data(data, pca):
        if '_id' in data.columns:
            data = data.drop('_id', axis=1)
        if 'ResponseTimeBinary' in data.columns:
            data = data.drop('ResponseTimeBinary', axis=1)

        # Select the necessary feature columns
        data = data[FEATURE_COLUMNS]

        # Transform the data using PCA if provided
        transformed_data = pca.transform(data) if pca else data
        return transformed_data

    # Make predictions task
    def make_predictions(ti):
        # Pull the model and PCA file paths from XCom
        model_path = ti.xcom_pull(task_ids='load_model_task', key='model_path')
        pca_path = ti.xcom_pull(task_ids='load_model_task', key='pca_path')
        raw_data = ti.xcom_pull(task_ids='fetch_data_task')

        # Load the model and PCA from file
        model = joblib.load(model_path)
        pca = joblib.load(pca_path)

        # Preprocess the raw data
        processed_data = preprocess_data(raw_data, pca)

        # Make predictions using the model
        predictions = model.predict(processed_data)
        return predictions


    make_predictions_task = PythonOperator(
        task_id='make_predictions_task',
        python_callable=make_predictions
    )

    # Store predictions in MongoDB task
    def store_predictions_in_mongodb(ti):
        mongo_uri = os.getenv('MONGO_URI')

        if not mongo_uri:
            raise ValueError("MONGO_URI environment variable not set.")

        client = MongoClient(mongo_uri)

        db = client['lfb']
        collection = db['lfb']

        # Fetch the predictions from XCom
        predictions = ti.xcom_pull(task_ids='make_predictions_task')
        prediction_docs = [{"prediction": pred, "timestamp": datetime.now()} for pred in predictions]
        
        # Insert the predictions into MongoDB
        collection.insert_many(prediction_docs)
        print(f"Inserted {len(prediction_docs)} predictions into MongoDB.")

    store_predictions_task = PythonOperator(
        task_id='store_predictions_task',
        python_callable=store_predictions_in_mongodb
    )

    # Define task dependencies
    load_model_task >> fetch_data_task >> make_predictions_task >> store_predictions_task
