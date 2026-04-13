# data-pipeline/Dockerfile
FROM apache/airflow:2.10.4-python3.11

# Switch to root to install system packages
USER root

# Install Java (required for Spark)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openjdk-17-jre-headless \
        procps \
        curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV SPARK_HOME=/opt/spark
ENV PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin

# Install Airflow providers + PySpark
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Download and install Spark (latest 3.5.x)
RUN mkdir -p ${SPARK_HOME} && \
    curl -s https://dlcdn.apache.org/spark/ | \
    grep -oP 'spark-3\.5\.[0-9]+' | sort -V | tail -1 | \
    xargs -I {} curl -L -o spark.tgz https://dlcdn.apache.org/spark/{}/{}-bin-hadoop3.tgz && \
    tar xzf spark.tgz --directory ${SPARK_HOME} --strip-components 1 && \
    rm spark.tgz

# Fix permissions
RUN chown -R airflow:airflow ${SPARK_HOME}

# Switch back to airflow user
USER airflow

# Optional: Copy your custom Spark config (if you have one)
# COPY spark-defaults.conf $SPARK_HOME/conf/

# Expose Spark ports (useful if running Spark master/worker)
EXPOSE 7077 8080 4040