FROM apache/airflow:3.1.7

# Install system dependencies for compilation
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy your clean requirements
COPY requirements.txt /opt/airflow/requirements.txt

USER airflow

# Install with Airflow constraints (critical for compatibility)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
       -r /opt/airflow/requirements.txt \
       --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.1.7/constraints-3.12.txt"