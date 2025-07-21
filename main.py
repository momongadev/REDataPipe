import os
import requests
import pandas as pd
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

url_ = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=COIN,CRYPTO:BTC&time_from=20220410T0130&limit=1000&apikey={os.getenv('ALPHA_VANTAGE_API_KEY')}"
bucket_name_ = "redatapipe-1"
region_ = "us-east-1"


def get_data(url):
    """Fetch data from the Alpha Vantage API."""
    url = r = requests.get(url)
    data = r.json()

    os.makedirs("data", exist_ok=True)

    df = pd.json_normalize(data)
    df.to_csv(f"data/coin_news_sentiment.csv", index=False)
    print("Data saved to data/coin_news_sentiment.csv")

def create_bucket(bucket_name, region=None):
    """"Create and S3 bucket in a specified region."""
    # Use default AWS credentials (will work with SSO after login)
    session = boto3.Session(profile_name='dev-profile')
    s3_client = session.client('s3', region_name=region)
    try:
        if region is None or region == 'us-east-1':
            # us-east-1 is the default region and doesn't require LocationConstraint
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            location = {'LocationConstraint': region}
            s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
        
        print(f"Bucket {bucket_name} created successfully.")
        buckets = s3_client.list_buckets()
        for b in buckets['Buckets']:
            print(f" - {b['Name']}")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'BucketAlreadyExists':
            print(f"Bucket {bucket_name} already exists and is owned by another account.")
            return False
        elif error_code == 'BucketAlreadyOwnedByYou':
            print(f"Bucket {bucket_name} already exists and is owned by you.")
            return True
        else:
            print(f"Error creating bucket {bucket_name}: {e}")
            return False
    return True

def upload_file_to_s3(file_name, bucket, object_name=None, region=None, data_type="raw", use_timestamp=True):
    """Upload a file to an S3 bucket with organized data type and date structure"""
    if object_name is None:
        object_name = os.path.basename(file_name)
    
    # Create organized folder structure: data_type/YYYY/MM/DD/
    if use_timestamp:
        now = datetime.now()
        date_path = now.strftime("%Y/%m/%d")
        timestamp_suffix = now.strftime("_%Y%m%d_%H%M%S")
        
        file_extension = os.path.splitext(object_name)[1]
        base_name = os.path.splitext(object_name)[0]
        
        # Structure: data_type/YYYY/MM/DD/filename_YYYYMMDD_HHMMSS.ext
        object_name = f"{data_type}/{date_path}/{base_name}{timestamp_suffix}{file_extension}"
    else:
        # Structure: data_type/filename.ext
        object_name = f"{data_type}/{object_name}"
    
    session = boto3.Session(profile_name='dev-profile')
    s3_client = session.client('s3', region_name=region)
    
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
        print(f"File {file_name} uploaded to bucket {bucket} as {object_name}.")
    except ClientError as e:
        print(f"Error uploading file {file_name} to bucket {bucket}: {e}")
        return False
    return True

# Execute the data pipeline
if __name__ == "__main__":
    # Step 1: Fetch data from Alpha Vantage API
    get_data(url_)
    
    # Step 2: Create S3 bucket
    create_bucket(bucket_name_, region_)
    
    # Step 3: Upload the CSV file to S3 
    csv_file_path = "data/coin_news_sentiment.csv"
    upload_file_to_s3(csv_file_path, bucket_name_, region=region_, data_type="news-sentiment")
