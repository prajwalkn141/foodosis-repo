import boto3
from dotenv import load_dotenv
import os

load_dotenv()  # Load credentials from .env file

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
print("AWS_ACCESS_KEY_ID from env:", AWS_ACCESS_KEY_ID)


s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name=AWS_REGION
)

def create_s3_bucket(bucket_name='foodosis-files'):
    try:
        create_args = {
            'Bucket': bucket_name,
            'ObjectOwnership': 'BucketOwnerEnforced'  # Disables ACLs for modern S3, ensures private
        }
        if AWS_REGION != 'us-east-1':
            create_args['CreateBucketConfiguration'] = {'LocationConstraint': AWS_REGION}
        s3_client.create_bucket(**create_args)
        print(f"S3 bucket '{bucket_name}' created successfully.")
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"S3 bucket '{bucket_name}' already exists.")
    except Exception as e:
        print(f"Error creating S3 bucket: {e}")

if __name__ == "__main__":
    create_s3_bucket()