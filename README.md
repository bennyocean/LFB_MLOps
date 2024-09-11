# London Fire Brigade

## Description
The London Fire Brigade (LFB) Response Time project is dedicated to analyzing, predicting, and optimizing the response times of the LFB, the busiest fire and rescue service in the United Kingdom and one of the largest in the world. Swift and precise responses are vital for mitigating damage caused by fires and other emergencies.

## Prerequisites
Before getting started, ensure you have the following installed:
- [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/DataScientest-Studio/AUG24-BMLOPS-INT-LFB.git
cd AUG24-BMLOPS-INT-LFB
```

### 2. Create the Conda Environment
Use the provided `environment.yaml` file to create the environment:

```bash
conda env create -f environment.yaml
```

### 3. Activate the Environment
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

## Contributing
Provide guidelines on how others can contribute to your project.

## License
Include information about the license for your project.
```
