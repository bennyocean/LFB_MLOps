from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mongo.hooks.mongo import MongoHook
from datetime import datetime, timedelta
import joblib
import pymongo
import pandas as pd

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2023, 9, 25),
}

# Define the DAG
with DAG('predict_model_dag',
         default_args=default_args,
         schedule_interval='@daily',
         catchup=False) as dag:

    def load_model():
        """Load the model from a .pkl file."""
        model = joblib.load('/path/to/your/model.pkl')
        return model

    def fetch_data_from_mongodb():
        """Fetch data from MongoDB Atlas."""
        mongo_conn_id = 'mongo_conn'
        mongo_hook = MongoHook(mongo_conn_id)
        client = mongo_hook.get_conn()

        # Replace with your MongoDB Atlas database and collection
        db = client['your_db_name']
        collection = db['your_collection_name']

        # Example: Fetch data to make predictions on
        data = pd.DataFrame(list(collection.find()))
        return data

    def make_predictions(ti):
        """Make predictions using the model."""
        model = ti.xcom_pull(task_ids='load_model_task')
        data = ti.xcom_pull(task_ids='fetch_data_task')

        # Make predictions
        predictions = model.predict(data)
        return predictions

    def store_predictions_in_mongodb(ti):
        """Store predictions back into MongoDB."""
        mongo_conn_id = 'mongo_conn'
        mongo_hook = MongoHook(mongo_conn_id)
        client = mongo_hook.get_conn()

        # Pull predictions from XCom
        predictions = ti.xcom_pull(task_ids='make_predictions_task')

        # Replace with your MongoDB Atlas database and collection
        db = client['your_db_name']
        collection = db['predictions_collection']

        # Insert predictions into MongoDB
        collection.insert_many(predictions)

    # Define the tasks
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
    load_model_task >> fetch_data_task >> make_predictions_task >> store_predictions_task
