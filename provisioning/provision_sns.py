import boto3
from dotenv import load_dotenv
import os

load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
SNS_EMAIL = os.getenv('SNS_EMAIL')

sns_client = boto3.client(
    'sns',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name=AWS_REGION
)

def create_sns_topic(topic_name='foodosis-notifications'):
    try:
        response = sns_client.create_topic(Name=topic_name)
        topic_arn = response['TopicArn']
        sns_client.subscribe(TopicArn=topic_arn, Protocol='email', Endpoint=SNS_EMAIL)
        print(f"SNS topic '{topic_arn}' created and subscribed to {SNS_EMAIL}.")
        print("Check your email for confirmation link and confirm the subscription.")
        print("Update .env with SNS_TOPIC_ARN=" + topic_arn)
        return topic_arn
    except Exception as e:
        print(f"Error creating SNS topic: {e}")
        return None

if __name__ == "__main__":
    create_sns_topic()