import boto3
from app.config import Config

# Global S3 client (will be updated dynamically)
s3_client = boto3.client(
    's3',
    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
    region_name=Config.AWS_REGION
)

def update_s3_client(access_key, secret_key, session_token, region):
    global s3_client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name=region
    )

def upload_file(file, key):
    if not Config.S3_BUCKET or not isinstance(Config.S3_BUCKET, str):
        raise ValueError("S3_BUCKET is not configured correctly in config")
    s3_client.upload_fileobj(file, Config.S3_BUCKET, key)
    return key

def get_file_url(key):
    if not Config.S3_BUCKET or not isinstance(Config.S3_BUCKET, str):
        raise ValueError("S3_BUCKET is not configured correctly in config")
    return s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': Config.S3_BUCKET, 'Key': key},
        ExpiresIn=3600
    )

def delete_file(key):
    """Deletes a file from the S3 bucket."""
    if not Config.S3_BUCKET or not isinstance(Config.S3_BUCKET, str):
        raise ValueError("S3_BUCKET is not configured correctly in config")
    s3_client.delete_object(Bucket=Config.S3_BUCKET, Key=key)
    return True # Indicate successful deletion
