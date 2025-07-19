import boto3
from dotenv import load_dotenv
import os

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

events_client = boto3.client(
    'events',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name=AWS_REGION
)

def enable_cloudwatch_rules():
    try:
        events_client.enable_rule(Name='daily_stock_check')
        events_client.enable_rule(Name='daily_expiration_check')
        print("CloudWatch rules enabled for app runtime.")
    except Exception as e:
        print(f"Error enabling CloudWatch rules: {e}")

if __name__ == "__main__":
    enable_cloudwatch_rules()