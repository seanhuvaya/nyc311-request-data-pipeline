# NYC 311 Data Pipeline
![Live](https://img.shields.io/badge/Live%20Demo-Available-brightgreen)
🚀 API: https://api.nyc311.seanhuvaya.dev/redoc
📊 Dashboard: https://nyc311.seanhuvaya.dev 

## Overview
This project implements an end-to-end data engineering pipeline that processes NYC 311 service request data into a structured analytics platform. The system ingests raw data, transforms it through a medallion architecture, and exposes curated datasets through APIs and dashboards.

The goal is to demonstrate a production-style data pipeline with orchestration, layered storage, and a serving layer for analytics consumption.

## Architecture
![Architecture Diagram](./docs/NYC%20311%20Data%20Pipeline%20Architecture.png)

The system follows a medallion-style data architecture with a clear separation between ingestion, storage, and serving layers.
