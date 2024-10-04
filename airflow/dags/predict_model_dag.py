from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime, timedelta
import joblib
import pandas as pd
from app.features import FEATURE_COLUMNS
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

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

        # Push the paths to XCom
        ti.xcom_push(key='model_path', value=model_path)
        ti.xcom_push(key='pca_path', value=pca_path)


    load_model_task = PythonOperator(
        task_id='load_model_task',
        python_callable=load_model
    )

    # Fetch data from MongoDB
    def fetch_data_from_mongodb():
        try:
            # Fetch MongoDB connection details from Airflow connections
            connection = BaseHook.get_connection('mongo_conn')  
            mongo_uri = connection.get_uri()

            if not mongo_uri:
                raise ValueError("MongoDB URI not found in Airflow connection.")

            # Connect to MongoDB and fetch data
            client = MongoClient(mongo_uri)
            db = client['lfb']
            collection = db['lfb']
            data = pd.DataFrame(list(collection.find()))

            if '_id' in data.columns:
                data['_id'] = data['_id'].apply(lambda x: str(x) if isinstance(x, ObjectId) else x)

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

    def make_predictions(ti):
        # Pull the model and PCA paths from XCom
        model_path = ti.xcom_pull(task_ids='load_model_task', key='model_path')
        pca_path = ti.xcom_pull(task_ids='load_model_task', key='pca_path')

        # Load the actual model and PCA objects using joblib
        model = joblib.load(model_path)
        pca = joblib.load(pca_path)

        # Fetch data from XCom
        raw_data = ti.xcom_pull(task_ids='fetch_data_task')

        if 'ResponseTimeBinary' in raw_data.columns:
            target_value = raw_data['ResponseTimeBinary'].values[0]
        else:
            target_value = None

        random_row = raw_data.sample(n=1)
        processed_data = preprocess_data(random_row, pca)
        prediction = model.predict(processed_data)[0]  

        if target_value is not None:
            comparison_result = (prediction == target_value)
            print(f"Prediction: {prediction}, Actual: {target_value}, Match: {comparison_result}")
        else:
            print("No target value to compare.")

        # Connect to MongoDB
        connection = BaseHook.get_connection('mongo_conn')
        mongo_uri = connection.get_uri()
        client = MongoClient(mongo_uri)
        db = client['lfb']
        collection = db['predictions']

        # Prepare document to insert into MongoDB
        prediction_doc = {
            "prediction": int(prediction),
            "input_data": random_row.to_dict(orient='records')[0],  
            "timestamp": datetime.now(),
            "actual_target": int(target_value) if target_value is not None else None,  
            "match": bool(comparison_result) if target_value is not None else None
        }

        # Insert the prediction into MongoDB
        collection.insert_one(prediction_doc)


    make_predictions_task = PythonOperator(
        task_id='make_predictions_task',
        python_callable=make_predictions
    )

    # Define task dependencies
    load_model_task >> fetch_data_task >> make_predictions_task
