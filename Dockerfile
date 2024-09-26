FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y wget bzip2

# Set the working directory
WORKDIR /home

# Copy application files
COPY ./app /home/app
COPY ./tests /home/tests
COPY ./model /home/model

# Ensure the logs directory exists
RUN mkdir -p /home/logs

# Copy requirements.txt and install dependencies directly
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Environment variable to enable logging
ENV LOG=1

# Expose the port
EXPOSE 8000

# Run FastAPI app directly
CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000", "--reload"]
