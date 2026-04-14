FROM python:3.11-slim-bookworm

USER root

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AIRFLOW_HOME=/opt/airflow \
    SPARK_HOME=/opt/spark

WORKDIR /opt/airflow

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bash \
        curl \
        procps \
        openjdk-17-jdk-headless \
        libpq-dev \
        gcc \
        g++ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a stable JAVA_HOME symlink based on the actual installed java location
RUN REAL_JAVA_HOME="$(dirname "$(dirname "$(readlink -f "$(which java)")")")" && \
    echo "Detected JAVA_HOME=${REAL_JAVA_HOME}" && \
    mkdir -p /usr/lib/jvm && \
    ln -sfn "${REAL_JAVA_HOME}" /usr/lib/jvm/java-17-openjdk && \
    ls -la /usr/lib/jvm/java-17-openjdk/bin/java

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk
ENV PATH="${JAVA_HOME}/bin:/usr/local/bin:/opt/spark/bin:/opt/spark/sbin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv pip install --system -r pyproject.toml

ENV SPARK_VERSION=4.1.1
RUN mkdir -p ${SPARK_HOME} && \
    curl -fL -o /tmp/spark.tgz \
      https://dlcdn.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz && \
    tar xzf /tmp/spark.tgz --directory ${SPARK_HOME} --strip-components 1 && \
    rm /tmp/spark.tgz

COPY . /opt/airflow

RUN useradd -ms /bin/bash -u 50000 airflow && \
    chown -R airflow:airflow /opt/airflow /opt/spark

USER airflow

EXPOSE 8080 8793 4040

CMD ["airflow", "version"]