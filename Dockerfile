FROM apache/airflow:3.1.7

USER root

# 1. Install Java and Procps (procps is required by Spark for process management)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    procps \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Download and install Spark binaries
# Ensure this version matches the image 'spark:python3' you used in docker-compose
ENV SPARK_VERSION=3.5.0
ENV HADOOP_VERSION=3
RUN curl -L https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz -o /tmp/spark.tgz && \
    tar -xzf /tmp/spark.tgz -C /opt/ && \
    mv /opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} /opt/spark && \
    rm /tmp/spark.tgz

# 3. Download hadoop-aws and aws-java-sdk-bundle JARs (must match Hadoop 3.3.4 bundled with Spark 3.5.0)
RUN curl -L https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar \
      -o /opt/spark/jars/hadoop-aws-3.3.4.jar && \
    curl -L https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar \
      -o /opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar

# Ensure the airflow user has full access to the Spark binaries
RUN chown -R airflow:root /opt/spark && chmod -R 755 /opt/spark

# Set these CRITICAL variables
ENV SPARK_HOME=/opt/spark
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
# Note: In Spark 3.5.0, the py4j file is usually py4j-0.10.9.7-src.zip
ENV PYTHONPATH="${SPARK_HOME}/python:${SPARK_HOME}/python/lib/py4j-0.10.9.7-src.zip:${PYTHONPATH}"
ENV PYSPARK_PYTHON=/usr/local/bin/python
ENV PYSPARK_DRIVER_PYTHON=/usr/local/bin/python

# Add Spark bins to the system PATH
ENV PATH="${SPARK_HOME}/bin:${PATH}"

USER airflow

COPY requirements.txt /opt/airflow/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /opt/airflow/requirements.txt