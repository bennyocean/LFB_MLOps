# London Fire Brigade

## Description
The London Fire Brigade (LFB) Response Time project is dedicated to analyzing, predicting, and optimizing the response times of the LFB, the busiest fire and rescue service in the United Kingdom and one of the largest in the world. Swift and precise responses are vital for mitigating damage caused by fires and other emergencies.

## Prerequisites
Before getting started, ensure you have the following installed:
- [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

## Setup Instructions

### Clone the Repository
```bash
git clone https://github.com/DataScientest-Studio/AUG24-BMLOPS-INT-LFB.git
cd AUG24-BMLOPS-INT-LFB
```

### Create the Conda Environment
Use the provided `environment.yaml` file to create the environment:

```bash
conda env create -f environment.yaml
```

### Activate the Environment
Activate the Conda environment before running any scripts:

```bash
conda activate lfb_env
```

## Updating the Conda Environment
If you add new dependencies or want to update the environment, you can export the updated environment:

```bash
conda env export > environment.yaml
```

Share this updated `environment.yaml` with your teammates to keep the environment consistent.

## Building and Running Containers

To build and run the containers, execute the following command:

```bash
docker-compose up --build
```

This command will:
- Build the images defined in the `docker-compose.yml`.
- Start two services:
  - The **API** service, which is built on a FastAPI.
  - The **MongoDB** service, which connects to a remote MongoDB instance.

### Accessing the Services
- **API**: Access the FastAPI server at [http://localhost:8000](http://localhost:8000).

### Stopping the Containers
To stop the running containers, you can use:

```bash
docker-compose down
```

This will stop and remove all containers defined in the `docker-compose.yml`.

## Airflow
- Starting the **Webserver**: 
```bash 
airflow webserver --port 8080
```
- Starting the **scheduler**: 
```bash 
airflow scheduler
```
- Start these in two different terminals
- Access the interface at [http://localhost:8080](http://localhost:8080).

## Monitoring & Logging

To ensure the operational health and performance of the LFB API, we have integrated **Prometheus** for metrics collection and **Grafana** for metrics visualization.

### Prometheus Setup
Prometheus is used for collecting metrics from the API. To access Prometheus:

1. Make sure the containers are spun up
2. Access Prometheus in your browser at [http://localhost:9090](http://localhost:9090)

### Grafana Setup
Grafana is used for visualizing metrics collected by Prometheus.

1. Access Prometheus in your browser at [http://localhost:3000](http://localhost:3000)
2. Credentials stored in GitHub Secrets allow for automated login.
3. Import Grafana dashboard config file (grafana_dashboard/my_dashboard.json) to set up dashboard.
4. Explore the following API key metrics in Grafana:
  - **API Request Latency Over Time:** Tracks the response time of API requests, helping to monitor performance and spot potential bottlenecks.
  - **CPU Usage:** Measures CPU consumption to ensure the API isn’t overloaded, which could affect response times and overall system stability.
  - **API Error Rate (4xx/5xx status codes):** Monitors the rate of client (4xx) and server (5xx) errors to help identify bugs or issues that affect the API's functionality.

## Contributing
Provide guidelines on how others can contribute to your project.

## License
Include information about the license for your project.
```