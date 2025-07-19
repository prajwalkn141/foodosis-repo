import boto3
from app.config import Config  # Load SNS topic ARN from config.py

sns_client = boto3.client(
    'sns',
    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
    region_name=Config.AWS_REGION
)

def publish_notification(message):
    sns_client.publish(
        TopicArn=Config.SNS_TOPIC_ARN,
        Message=message,
        Subject='Foodosis Inventory Alert'  # Email subject
    )