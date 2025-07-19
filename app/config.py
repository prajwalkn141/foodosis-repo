import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env

class Config:
    RDS_HOST = os.getenv('RDS_HOST')
    RDS_PORT = os.getenv('RDS_PORT')
    RDS_DB = os.getenv('RDS_DB')
    RDS_USER = os.getenv('RDS_USER')
    RDS_PASSWORD = os.getenv('RDS_PASSWORD')
    
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
    AWS_REGION = os.getenv('AWS_REGION')
    
    S3_BUCKET = os.getenv('S3_BUCKET')
    SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN')
    
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Debug prints to verify loading (remove after testing)
    print(f"Loaded AWS_ACCESS_KEY_ID: {AWS_ACCESS_KEY_ID}")  # Should show your key
    print(f"Loaded AWS_SESSION_TOKEN: {AWS_SESSION_TOKEN}")  # Should show your token
    print(f"Loaded S3_BUCKET: {S3_BUCKET}")  # Should show 'foodosis-files'

    # Required check (raise error if missing)
    if not all([RDS_HOST, RDS_PORT, RDS_DB, RDS_USER, RDS_PASSWORD, S3_BUCKET, SECRET_KEY]):
        raise ValueError("Missing required environment variables in .env")