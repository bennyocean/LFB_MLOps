from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mongo.hooks.mongo import MongoHook
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

def ensure_mongo_connection():
    from airflow.models import Connection
    from airflow import settings

    session = settings.Session()
    mongo_conn = session.query(Connection).filter(Connection.conn_id == 'mongo_conn').first()
    
    if mongo_conn and mongo_conn.conn_type != 'mongo':
        mongo_conn.conn_type = 'mongo'
        session.add(mongo_conn)
        session.commit()
        logging.warning("Mongo connection type updated to 'mongo'.")
    else:
        logging.warning(f"Mongo connection is already set correctly or does not exist. Conn_type: {mongo_conn.conn_type if mongo_conn else 'None'}")
    logging.warning(f"conn_type = {mongo_conn.conn_type if mongo_conn else 'None'}")
    session.close()

# Define the DAG
with DAG('predict_model_dag',
         default_args=default_args,
         schedule='@daily',
         catchup=False) as dag:
    
    ensure_mongo_conn_task = PythonOperator(
        task_id='ensure_mongo_conn_task',
        python_callable=ensure_mongo_connection
)

    # Test MongoDB connection task
    def test_mongo_connection():
        try:
            connection = BaseHook.get_connection('mongo_conn')
            print(f"Connection URI: {connection.get_uri()}")
            print("MongoDB connection works correctly.")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")

    # Load model and PCA task
    def load_model(ti):
        dag_file_directory = os.path.dirname(os.path.realpath(__file__))
        model_path = os.path.join(dag_file_directory, '../../model/model.pkl')
        pca_path = os.path.join(dag_file_directory, '../../model/pca.pkl')

        model = joblib.load(model_path)
        pca = joblib.load(pca_path)

        # Push model and PCA to XCom for later use
        ti.xcom_push(key='model', value=model)
        ti.xcom_push(key='pca', value=pca)

    # Fetch data from MongoDB task
    def fetch_data_from_mongodb():
        try:
            mongo_uri = os.getenv('MONGO_URI')

            if not mongo_uri:
                raise ValueError("MONGO_URI environment variable not set.")

            client = MongoClient(mongo_uri)

            db = client['lfb']
            collection = db['lfb']

            data = pd.DataFrame(list(collection.find()))
            return data

        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise


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
        # Pull the model and PCA from XCom
        model = ti.xcom_pull(task_ids='load_model_task', key='model')
        pca = ti.xcom_pull(task_ids='load_model_task', key='pca')
        raw_data = ti.xcom_pull(task_ids='fetch_data_task')

        # Preprocess the raw data
        processed_data = preprocess_data(raw_data, pca)

        # Make predictions using the model
        predictions = model.predict(processed_data)
        return predictions

    # Store predictions in MongoDB task
    def store_predictions_in_mongodb(ti):
        mongo_hook = MongoHook(mongo_conn_id='mongo_conn') 
        client = mongo_hook.get_conn()

        db = client['lfb']
        collection = db['predictions']

        # Fetch the predictions from XCom
        predictions = ti.xcom_pull(task_ids='make_predictions_task')
        prediction_docs = [{"prediction": pred, "timestamp": datetime.now()} for pred in predictions]
        
        # Insert the predictions into MongoDB
        collection.insert_many(prediction_docs)
        print(f"Inserted {len(prediction_docs)} predictions into MongoDB.")

    # Define the tasks in the DAG
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

    # Define task dependencies
    ensure_mongo_conn_task >> test_mongo_conn_task >> load_model_task >> fetch_data_task >> make_predictions_task >> store_predictions_task
