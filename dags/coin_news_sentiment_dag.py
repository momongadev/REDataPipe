import os
import requests
import pandas as pd
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta, timezone
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

# Default arguments for the DAG
default_args = {
    'owner': 'data-engineer',
    'depends_on_past': False,
    'start_date': datetime.now(timezone.utc) - timedelta(days=1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Initialize the DAG
dag = DAG(
    'coin_news_sentiment_pipeline',
    default_args=default_args,
    description='Fetch coin news sentiment data every 6 hours and upload to S3',
    schedule=timedelta(hours=6),  # Run every 6 hours
    catchup=False,
    tags=['crypto', 'news', 'sentiment', 's3'],
)

# Configuration
BUCKET_NAME = "redatapipe-1"
REGION = "us-east-1"
DATA_DIR = "/opt/airflow/data"
CSV_FILE_PATH = f"{DATA_DIR}/coin_news_sentiment.csv"


def fetch_news_sentiment_data(**context):
    """
    Fetch cryptocurrency news sentiment data from Alpha Vantage API
    """
    # Get API key from environment variable
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY environment variable is not set")
    
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=COIN,CRYPTO:BTC&time_from=20220410T0130&limit=1000&apikey={api_key}"
    
    print(f"Fetching data from Alpha Vantage API...")
    response = requests.get(url)
    response.raise_for_status()
    
    data = response.json()
    
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Convert to DataFrame and save
    df = pd.json_normalize(data)
    df.to_csv(CSV_FILE_PATH, index=False)
    
    print(f"Data successfully saved to {CSV_FILE_PATH}")
    print(f"Retrieved {len(df)} records")
    
    return CSV_FILE_PATH


def create_s3_bucket(**context):
    """
    Create S3 bucket if it doesn't exist
    """
    # use aws credentials from the dev profile, must have loged in with aws sso login
    session = boto3.Session(profile_name='dev-profile')
    s3_client = session.client('s3', region_name=REGION)
    
    try:
        if REGION is None or REGION == 'us-east-1':
            # us-east-1 is the default region
            s3_client.create_bucket(Bucket=BUCKET_NAME)
        else:
            location = {'LocationConstraint': REGION}
            s3_client.create_bucket(Bucket=BUCKET_NAME, CreateBucketConfiguration=location)
        
        print(f"Bucket {BUCKET_NAME} created successfully.")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'BucketAlreadyExists':
            print(f"Bucket {BUCKET_NAME} already exists and is owned by another account.")
            raise
        elif error_code == 'BucketAlreadyOwnedByYou':
            print(f"Bucket {BUCKET_NAME} already exists and is owned by you.")
        else:
            print(f"Error creating bucket {BUCKET_NAME}: {e}")
            raise
    
    # List buckets to confirm
    buckets = s3_client.list_buckets()
    print("Available buckets:")
    for bucket in buckets['Buckets']:
        print(f" - {bucket['Name']}")
    
    return True


def upload_to_s3(**context):
    """
    Upload the CSV file to S3 with organized folder structure
    """
    file_name = CSV_FILE_PATH
    object_name = os.path.basename(file_name)
    data_type = "news-sentiment"
    
    # Create organized folder structure: data_type/YYYY/MM/DD/
    now = datetime.now()
    date_path = now.strftime("%Y/%m/%d")
    timestamp_suffix = now.strftime("_%Y%m%d_%H%M%S")
    
    file_extension = os.path.splitext(object_name)[1]
    base_name = os.path.splitext(object_name)[0]
    
    # Structure: data_type/YYYY/MM/DD/filename_YYYYMMDD_HHMMSS.ext
    s3_object_name = f"{data_type}/{date_path}/{base_name}{timestamp_suffix}{file_extension}"
    
    session = boto3.Session(profile_name='dev-profile')
    s3_client = session.client('s3', region_name=REGION)
    
    try:
        response = s3_client.upload_file(file_name, BUCKET_NAME, s3_object_name)
        print(f"File {file_name} uploaded to bucket {BUCKET_NAME} as {s3_object_name}")
        
        # Log file info
        file_stats = os.stat(file_name)
        print(f"File size: {file_stats.st_size} bytes")
        
        return s3_object_name
        
    except ClientError as e:
        print(f"Error uploading file {file_name} to bucket {BUCKET_NAME}: {e}")
        raise


def cleanup_local_files(**context):
    """
    Clean up local CSV files after successful upload
    """
    try:
        if os.path.exists(CSV_FILE_PATH):
            os.remove(CSV_FILE_PATH)
            print(f"Cleaned up local file: {CSV_FILE_PATH}")
        else:
            print(f"File {CSV_FILE_PATH} does not exist, nothing to clean up")
    except Exception as e:
        print(f"Warning: Could not clean up file {CSV_FILE_PATH}: {e}")


# Define tasks
task_fetch_data = PythonOperator(
    task_id='fetch_news_sentiment_data',
    python_callable=fetch_news_sentiment_data,
    dag=dag,
)

task_create_bucket = PythonOperator(
    task_id='create_s3_bucket',
    python_callable=create_s3_bucket,
    dag=dag,
)

task_upload_to_s3 = PythonOperator(
    task_id='upload_to_s3',
    python_callable=upload_to_s3,
    dag=dag,
)

task_cleanup = PythonOperator(
    task_id='cleanup_local_files',
    python_callable=cleanup_local_files,
    dag=dag,
    trigger_rule='none_failed',  # run if no upstream tasks failed
)

# Define task dependencies
task_fetch_data >> task_create_bucket >> task_upload_to_s3 >> task_cleanup