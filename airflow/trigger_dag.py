import time
import requests
from bs4 import BeautifulSoup

# URL der Airflow API und Login-Daten
airflow_url = "http://localhost:8080"
login_url = f"{airflow_url}/login/"
dag_run_url = f"{airflow_url}/api/v1/dags/retrain_model_dag/dagRuns"
dag_run_status_url = f"{airflow_url}/api/v1/dags/retrain_model_dag/dagRuns/{{dag_run_id}}"

# Start einer Session
session = requests.Session()

# Abrufen der Login-Seite, um den CSRF-Token zu erhalten
login_page_response = session.get(login_url)
if login_page_response.status_code == 200:
    # CSRF-Token aus dem HTML extrahieren
    soup = BeautifulSoup(login_page_response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
    print("CSRF-Token erhalten:", csrf_token)
else:
    print(f"Fehler beim Abrufen der Login-Seite: {login_page_response.status_code}")
    exit()

# Login-Daten
payload = {
    "username": "admin",
    "password": "psw",
    "csrf_token": csrf_token
}

# Login-Anfrage
login_response = session.post(login_url, data=payload)
if login_response.status_code == 200:
    print("Erfolgreich eingeloggt!")
else:
    print(f"Login fehlgeschlagen: {login_response.status_code}")
    print(f"Antwort: {login_response.text}")
    exit()

# Unpause the DAG before triggering
unpause_url = f"{airflow_url}/api/v1/dags/retrain_model_dag"
unpause_data = {"is_paused": False}
unpause_response = session.patch(unpause_url, json=unpause_data)

if unpause_response.status_code == 200:
    print("DAG erfolgreich entpausiert!")
else:
    print(f"Fehler beim Entpausieren des DAGs: {unpause_response.status_code}, {unpause_response.text}")
    exit()

# Trigger the DAG
dag_run_data = {"conf": {}}
trigger_response = session.post(dag_run_url, json=dag_run_data)

if trigger_response.status_code == 200:
    print("DAG erfolgreich getriggert!")
    dag_run_id = trigger_response.json()["dag_run_id"]
else:
    print(f"Fehler beim Triggern des DAGs: {trigger_response.status_code}, {trigger_response.text}")
    exit()

# Überwachung des DAG-Runs
def check_dag_run_status(dag_run_id):
    status_url = dag_run_status_url.format(dag_run_id=dag_run_id)
    response = session.get(status_url)
    if response.status_code == 200:
        return response.json()["state"]
    else:
        return None

# Warte, bis der DAG erfolgreich abgeschlossen ist
while True:
    status = check_dag_run_status(dag_run_id)
    if status in ["success", "failed"]:
        print(f"DAG-Run abgeschlossen mit Status: {status}")
        break
    else:
        print(f"DAG-Run Status: {status}, warte auf Abschluss...")
    time.sleep(30)  # 30 Sekunden warten, bevor erneut geprüft wird

