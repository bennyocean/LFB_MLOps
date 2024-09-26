FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y wget bzip2

# Detect architecture and install correct Miniconda version
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh ; \
    else \
        wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -O ~/miniconda.sh ; \
    fi && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    /opt/conda/bin/conda clean -a && \
    ln -s /opt/conda/bin/conda /usr/bin/conda

# Initialize Conda for bash
RUN /opt/conda/bin/conda init bash

# Set path to Conda
ENV PATH=/opt/conda/bin:$PATH

WORKDIR /app

# Copy the rest of the project files
COPY ./app /app
COPY ./tests /app/tests
COPY ./model/model.pkl /app/model/model.pkl

# Ensure the logs directory exists
RUN mkdir -p /app/logs

# Copy environment.yml and create conda environment
COPY clean_environment.yml environment.yml
RUN conda env create -f environment.yml
SHELL ["/bin/bash", "-c"]

# Environment variable to enable logging
ENV LOG=1

# Expose port
EXPOSE 8000

# Run FastAPI app with activated Conda environment
CMD ["/bin/bash", "-c", "source activate clean_env && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]
#CMD ["uvicorn", "main:app", "--host=0.0.0.0" , "--reload" , "--port", "8000"]
