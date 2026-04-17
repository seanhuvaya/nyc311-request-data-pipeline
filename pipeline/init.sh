#!/usr/bin/env bash
set -e

# Fix permissions
mkdir -p /opt/airflow/{dags,logs,plugins}
chown -R ${AIRFLOW_UID:-50000}:0 /opt/airflow
chmod -R 775 /opt/airflow/logs

# Migrate DB
airflow db migrate

# Create admin user if it doesn't exist
if ! airflow users list | grep -q "${AIRFLOW_ADMIN_USER}"; then
    echo "Creating admin user: ${AIRFLOW_ADMIN_USER}"
    airflow users create \
      --username "${AIRFLOW_ADMIN_USER}" \
      --password "${AIRFLOW_ADMIN_PASSWORD}" \
      --firstname "${AIRFLOW_ADMIN_FIRSTNAME}" \
      --lastname "${AIRFLOW_ADMIN_LASTNAME}" \
      --role Admin \
      --email "${AIRFLOW_ADMIN_EMAIL}"
    echo "✅ Admin user created successfully"
else
    echo "✅ Admin user ${AIRFLOW_ADMIN_USER} already exists"
fi