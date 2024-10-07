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

load_dotenv()

default_args = {
    'owner': 'airflow',
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2023, 9, 25),
}

with DAG('predict_model_dag',
         default_args=default_args,
         schedule='@daily',
         catchup=False) as dag:

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
                raise ValueError("MongoDB URI not found in mongo_conn.")

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

    def preprocess_data(data, pca):
        if '_id' in data.columns:
            data = data.drop('_id', axis=1)
        if 'ResponseTimeBinary' in data.columns:
            data = data.drop('ResponseTimeBinary', axis=1)

        data = data[FEATURE_COLUMNS]

        transformed_data = pca.transform(data) if pca else data
        return transformed_data

    def make_predictions(ti):
        model_path = ti.xcom_pull(task_ids='load_model_task', key='model_path')
        pca_path = ti.xcom_pull(task_ids='load_model_task', key='pca_path')

        model = joblib.load(model_path)
        pca = joblib.load(pca_path)

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

        connection = BaseHook.get_connection('mongo_conn')
        mongo_uri = connection.get_uri()
        client = MongoClient(mongo_uri)
        db = client['lfb']
        collection = db['predictions']

        prediction_doc = {
            "prediction": int(prediction),
            "input_data": random_row.to_dict(orient='records')[0],
            "timestamp": datetime.now(),
            "actual_target": int(target_value) if target_value is not None else None,
            "match": bool(comparison_result) if target_value is not None else None
        }

        collection.insert_one(prediction_doc)

    make_predictions_task = PythonOperator(
        task_id='make_predictions_task',
        python_callable=make_predictions
    )

    load_model_task >> fetch_data_task >> make_predictions_task
