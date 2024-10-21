## Introduction

This repository contains the code for our Machine Learning Operation (MLOPs) project, focused on deploying, automating, and monitoring ML models to predict response times for the London Fire Brigade (LFB).

The project was developed as part of our [ML Engineering](https://datascientest.com/en/machine-learning-engineer-course) training at [DataScientest](https://datascientest.com/), in cooperation with [Panthéon-Sorbonne University](https://www.pantheonsorbonne.fr/). For an overview of the system's architecture and workflows, feel free to download the project's [presentation](./presentation/lfb_mlops_presentation.pdf).

Additionally, this repository follows up on the data preprocessing, analysis, and model development work. You can find the related repository [here](https://github.com/bennyocean/LFB_ResponseTimes_Prediction.git). 

This project was developed by the following team :
- Ismarah MAIER ([GitHub](https://github.com/isi-pizzy) / [LinkedIn](https://www.linkedin.com/in/ismarah-maier-18496613b/))
- René Gross ([GitHub](https://github.com/RenGross) / [LinkedIn](https://www.linkedin.com/in/rené-groß-013a2b20b/))
- Dr. Benjamin SCHELLINGER ([GitHub](https://github.com/bennyocean) / [LinkedIn](https://www.linkedin.com/in/benjaminschellinger/))

## Prerequisites
Before getting started, ensure you have the following installed:
- [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

## Setup Instructions

### Clone the Repository
```bash
git clone https://github.com/bennyocean/LFB_MLOps.git
cd AUG24-BMLOPS-INT-LFB
```

### Create the Conda Environment
Use the provided `environment.yaml` file to create the environment:

```bash
#for Mac/Linux OS
conda env create -f environment.yml
#for Windows OS
conda env create -f environment_win.yml
```

### Activate the Environment
Activate the Conda environment before running any scripts:

```bash
conda activate lfb_env
```

### Updating the Conda Environment
If you add new dependencies or want to update the environment, you can export the updated environment:

```bash
conda env export > environment.yaml
```

## Building & Running Containers

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

## Automation with Apache Airflow
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
3. You can import the Grafana dashboard using the following config file: [Import Grafana Dashboard](./grafana_dashboard/my_dashboard.json)

4. Explore the following API key metrics in Grafana:
  - **API Request Latency Over Time:** Tracks the response time of API requests, helping to monitor performance and spot potential bottlenecks.
  - **CPU Usage:** Measures CPU consumption to ensure the API isn’t overloaded, which could affect response times and overall system stability.
  - **API Error Rate (4xx/5xx status codes):** Monitors the rate of client (4xx) and server (5xx) errors to help identify bugs or issues that affect the API's functionality.