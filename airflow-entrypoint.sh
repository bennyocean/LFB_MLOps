#!/bin/bash
set -e

# Create directories if they don't exist
mkdir -p /opt/airflow/logs /opt/airflow/dags /opt/airflow/plugins

# Ensure the airflow user has write permissions to necessary directories
# chown -R "${AIRFLOW_UID}:${AIRFLOW_GID}" /opt/airflow/logs /opt/airflow/dags /opt/airflow/plugins /home/airflow

# Run the original command
# exec "$@"