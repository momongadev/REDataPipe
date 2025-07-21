# REDataPipe - Airflow Setup Guide

## Overview

This project sets up an Apache Airflow data pipeline that fetches cryptocurrency news sentiment data every 6 hours and uploads it to AWS S3.

## Prerequisites

- Docker and Docker Compose installed
- AWS CLI configured with your credentials (profile name: `dev-profile`)
- Alpha Vantage API key (already configured in `.env`)

## Quick Start

### 1. Start Airflow Services

```powershell
.\manage-airflow.ps1 start
```

### 2. Access Airflow Web UI

- Open your browser and go to: http://localhost:8080
- Username: `airflow`
- Password: `airflow`

### 3. Check DAG Status

```powershell
.\manage-airflow.ps1 dag-list
```

## DAG Details

### `coin_news_sentiment_pipeline`

- **Schedule**: Every 6 hours
- **Tasks**:
  1. `fetch_news_sentiment_data` - Fetches data from Alpha Vantage API
  2. `create_s3_bucket` - Ensures S3 bucket exists
  3. `upload_to_s3` - Uploads CSV file to S3 with timestamp
  4. `cleanup_local_files` - Removes local files after upload

### Data Flow

```
Alpha Vantage API → Local CSV → S3 Bucket
                                  ↓
                    s3://redatapipe-1/news-sentiment/YYYY/MM/DD/
```

## Configuration

### Environment Variables (`.env`)

- `ALPHA_VANTAGE_API_KEY`: Your API key for Alpha Vantage
- `AWS_PROFILE`: AWS profile name (dev-profile)
- `AIRFLOW_UID`: User ID for Airflow containers

### S3 Structure

Files are organized in S3 as:

```
redatapipe-1/
└── news-sentiment/
    └── 2024/
        └── 01/
            └── 15/
                └── coin_news_sentiment_20240115_143052.csv
```

## Common Commands

### Management Script Commands

```powershell
# Start services
.\manage-airflow.ps1 start

# Stop services
.\manage-airflow.ps1 stop

# View logs
.\manage-airflow.ps1 logs

# Check status
.\manage-airflow.ps1 status

# Test DAG
.\manage-airflow.ps1 dag-test

# Open web UI
.\manage-airflow.ps1 web

# Clean up everything
.\manage-airflow.ps1 cleanup
```

### Manual Docker Commands

```powershell
# Start all services
docker-compose up -d

# View logs for specific service
docker-compose logs airflow-scheduler

# Execute commands in container
docker-compose exec airflow-scheduler airflow dags list

# Stop all services
docker-compose down
```

## Monitoring

### Web UI Features

1. **DAGs View**: See all DAGs and their schedules
2. **Tree View**: Visual representation of task dependencies
3. **Graph View**: Flowchart of the pipeline
4. **Task Logs**: Detailed logs for each task execution

### Troubleshooting

#### Common Issues

1. **DAG not showing up**: Check logs for syntax errors
2. **API failures**: Verify Alpha Vantage API key
3. **S3 upload failures**: Check AWS credentials and bucket permissions
4. **Memory issues**: Ensure Docker has at least 4GB RAM allocated

#### Useful Commands

```powershell
# Check DAG syntax
docker-compose exec airflow-scheduler python /opt/airflow/dags/coin_news_sentiment_dag.py

# View scheduler logs
docker-compose logs airflow-scheduler

# Restart specific service
docker-compose restart airflow-scheduler
```

## File Structure

```
REDataPipe/
├── dags/
│   └── coin_news_sentiment_dag.py    # Main DAG definition
├── data/                             # Local data storage (temporary)
├── logs/                             # Airflow logs
├── config/
│   └── airflow.cfg                   # Airflow configuration
├── docker-compose.yml               # Docker services definition
├── .env                             # Environment variables
├── requirements.txt                 # Python dependencies
├── manage-airflow.ps1              # PowerShell management script
└── README_SETUP.md                 # This file
```

## Next Steps

1. Customize the DAG schedule if needed (currently every 6 hours)
2. Add data transformation tasks between fetch and upload
3. Set up email notifications for failures
4. Add data quality checks
5. Implement data lineage tracking
