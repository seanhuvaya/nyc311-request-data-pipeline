FROM python:3.11-slim-bookworm

USER root

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AIRFLOW_HOME=/opt/airflow \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    SPARK_HOME=/opt/spark \
    PATH="/usr/local/bin:/opt/spark/bin:/opt/spark/sbin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin"

WORKDIR /opt/airflow

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bash \
        curl \
        procps \
        openjdk-17-jre-headless \
        libpq-dev \
        gcc \
        g++ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy only dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies from pyproject.toml into system Python
RUN uv pip install --system -r pyproject.toml

ENV SPARK_VERSION=3.5.8
RUN mkdir -p ${SPARK_HOME} && \
    curl -fL -o /tmp/spark.tgz \
      https://dlcdn.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz && \
    tar xzf /tmp/spark.tgz --directory ${SPARK_HOME} --strip-components 1 && \
    rm /tmp/spark.tgz

# Copy the rest of the project
COPY . /opt/airflow

RUN useradd -ms /bin/bash -u 50000 airflow && \
    chown -R airflow:airflow /opt/airflow /opt/spark

USER airflow

EXPOSE 8080 8793 4040

CMD ["airflow", "version"]