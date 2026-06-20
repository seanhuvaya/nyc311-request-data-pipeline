FROM python:3.11-slim-bookworm

USER root

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AIRFLOW_HOME=/opt/airflow

WORKDIR /opt/airflow

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bash \
        curl \
        procps \
        libpq-dev \
        gcc \
        g++ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv pip install --system -r pyproject.toml

COPY . /opt/airflow

RUN useradd -ms /bin/bash -u 50000 airflow && \
    chown -R airflow:airflow /opt/airflow

USER airflow

EXPOSE 8080 8793

CMD ["airflow", "version"]