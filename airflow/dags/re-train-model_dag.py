from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime, timedelta
import joblib
import pandas as pd
from sklearn.ensemble import VotingClassifier, RandomForestClassifier
from sklearn.decomposition import PCA
from imblearn.under_sampling import RandomUnderSampler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import recall_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from pymongo import MongoClient
import logging
import os

default_args = {
    'owner': 'airflow',
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2023, 9, 25),
}

with DAG('retrain_model_dag',
         default_args=default_args,
         schedule_interval=None,
         catchup=False) as dag:

    def fetch_data_from_mongodb(ti):
        connection = BaseHook.get_connection('mongo_conn')
        mongo_uri = connection.get_uri()

        client = MongoClient(mongo_uri)
        db = client['lfb']
        collection = db['lfb']

        data = pd.DataFrame(list(collection.find()))
        data = data.drop(columns=['_id'], errors='ignore')

        model_dir = "/opt/airflow/model/"
        os.makedirs(model_dir, exist_ok=True)
        temp_file_path = os.path.join(model_dir, "fetched_data.csv")

        logging.info(f"Saving the data to {temp_file_path}")

        data.to_csv(temp_file_path, index=False)

        ti.xcom_push(key='data_file_path', value=temp_file_path)

    fetch_data_task = PythonOperator(
        task_id='fetch_data_task',
        python_callable=fetch_data_from_mongodb,
        do_xcom_push=True
    )

    def train_new_model(ti):
        temp_file_path = ti.xcom_pull(task_ids='fetch_data_task', key='data_file_path')
        logging.info(f"Loading data from {temp_file_path}")

        raw_data = pd.read_csv(temp_file_path, low_memory=False)

        if 'data' in raw_data.columns:
            logging.warning("'data' column found and will be dropped.")
            raw_data = raw_data.drop(columns=['data'])

        y = raw_data['ResponseTimeBinary']
        X = raw_data.drop(columns=['ResponseTimeBinary'], errors='ignore')

        combined = pd.concat([X, y], axis=1)
        combined_cleaned = combined.dropna()

        X_cleaned = combined_cleaned.drop(columns=['ResponseTimeBinary'])
        y_cleaned = combined_cleaned['ResponseTimeBinary']

        rUs = RandomUnderSampler(random_state=666)
        X_resampled, y_resampled = rUs.fit_resample(X_cleaned, y_cleaned)

        pca = PCA(n_components=0.85)
        X_resampled_pca = pca.fit_transform(X_resampled)

        X_train, X_test, y_train, y_test = train_test_split(X_resampled_pca, y_resampled, test_size=0.2, random_state=666)

        xgboost = XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.1, subsample=0.9, random_state=666)
        rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=666)
        logreg = LogisticRegression(C=5, random_state=666)

        voting_clf = VotingClassifier(estimators=[('XGboost', xgboost), ('RF', rf), ('LogReg', logreg)], voting='hard')
        voting_clf.fit(X_train, y_train)

        y_pred = voting_clf.predict(X_test)
        new_model_recall = recall_score(y_test, y_pred)

        model_path = "/opt/airflow/model/new_voting_model.pkl"
        pca_new_path = "/opt/airflow/model/pca_new.pkl"
        new_undersampler_path = "/opt/airflow/model/undersampler_new.pkl"
        joblib.dump(voting_clf, model_path)
        joblib.dump(pca, pca_new_path)
        joblib.dump(rUs, new_undersampler_path)

        ti.xcom_push(key='new_model_path', value=model_path)
        ti.xcom_push(key='pca_path', value=pca_new_path)
        ti.xcom_push(key='undersampler_path', value=new_undersampler_path)
        ti.xcom_push(key='new_model_recall', value=new_model_recall)

    train_model_task = PythonOperator(
        task_id='train_model_task',
        python_callable=train_new_model
    )

    def evaluate_and_overwrite(ti):
        temp_file_path = ti.xcom_pull(task_ids='fetch_data_task', key='data_file_path')

        if temp_file_path is None or not os.path.exists(temp_file_path):
            raise ValueError(f"No CSV file found at the expected path: {temp_file_path}")

        logging.info(f"Loading data from {temp_file_path}")
        raw_data = pd.read_csv(temp_file_path, low_memory=False)

        if 'data' in raw_data.columns:
            logging.warning("'data' column found and will be dropped.")
            raw_data = raw_data.drop(columns=['data'])

        y = raw_data['ResponseTimeBinary']
        X = raw_data.drop(columns=['ResponseTimeBinary'], errors='ignore')

        combined = pd.concat([X, y], axis=1)
        combined_cleaned = combined.dropna()

        X_cleaned = combined_cleaned.drop(columns=['ResponseTimeBinary'])
        y_cleaned = combined_cleaned['ResponseTimeBinary']

        # Old model paths
        model_path = "/opt/airflow/model/model.pkl"
        old_pca_path = "/opt/airflow/model/pca.pkl"
        old_undersampler_path = "/opt/airflow/model/old_undersampler.pkl"

        current_model = joblib.load(model_path)
        old_pca = joblib.load(old_pca_path)
        old_rUs = joblib.load(old_undersampler_path)

        # New model
        new_model_path = ti.xcom_pull(task_ids='train_model_task', key='new_model_path')
        new_model_recall = ti.xcom_pull(task_ids='train_model_task', key='new_model_recall')
        new_pca_path = ti.xcom_pull(task_ids='train_model_task', key='pca_path')
        new_undersampler_path = ti.xcom_pull(task_ids='train_model_task', key='undersampler_path')

        new_model = joblib.load(new_model_path)
        new_pca = joblib.load(new_pca_path)
        new_rUs = joblib.load(new_undersampler_path)

        X_resampled_old, y_resampled_old = old_rUs.fit_resample(X_cleaned, y_cleaned)
        X_resampled_pca_old = old_pca.transform(X_resampled_old)

        y_pred_current = current_model.predict(X_resampled_pca_old)
        current_model_recall = recall_score(y_resampled_old, y_pred_current)

        # Compare the recall scores
        if new_model_recall > current_model_recall:
            # Overwrite the model and PCA if the new one is better
            joblib.dump(new_model, model_path)
            joblib.dump(new_pca, old_pca_path)
            joblib.dump(new_rUs, old_undersampler_path)
            logging.info(f"New model with recall {new_model_recall} replaces the old model with recall {current_model_recall}")
        else:
            logging.info(f"Old model retained with recall {current_model_recall}. New model had {new_model_recall}.")

    evaluate_and_overwrite_task = PythonOperator(
        task_id='evaluate_and_overwrite_task',
        python_callable=evaluate_and_overwrite
    )

    def clean_up_temp_file(ti):
        temp_file_path = ti.xcom_pull(task_ids='fetch_data_task', key='data_file_path')
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"Temporary file {temp_file_path} deleted.")

    clean_up_task = PythonOperator(
        task_id='clean_up_task',
        python_callable=clean_up_temp_file,
        trigger_rule='all_done'
    )

    # Define task sequence
    fetch_data_task >> train_model_task >> evaluate_and_overwrite_task >> clean_up_task
