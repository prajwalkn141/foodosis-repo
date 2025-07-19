import boto3
from dotenv import load_dotenv
import os

load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
LAMBDA_STOCK_ARN = os.getenv('LAMBDA_STOCK_ARN')
LAMBDA_EXPIRATION_ARN = os.getenv('LAMBDA_EXPIRATION_ARN')

events_client = boto3.client(
    'events',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name=AWS_REGION
)

def create_cloudwatch_rule(rule_name, schedule, lambda_arn):
    try:
        # Create the rule
        response = events_client.put_rule(
            Name=rule_name,
            ScheduleExpression=schedule,  # e.g., 'cron(0 0 * * ? *)' for daily at midnight UTC
            State='ENABLED'
        )
        # Add the target (Lambda) to the rule
        events_client.put_targets(
            Rule=rule_name,
            Targets=[{'Id': '1', 'Arn': lambda_arn}]
        )
        print(f"CloudWatch rule '{rule_name}' created and targeted to Lambda {lambda_arn}.")
    except Exception as e:
        print(f"Error creating CloudWatch rule '{rule_name}': {e}")

if __name__ == "__main__":
    create_cloudwatch_rule('daily_stock_check', 'cron(0 0 * * ? *)', LAMBDA_STOCK_ARN)
    create_cloudwatch_rule('daily_expiration_check', 'cron(0 0 * * ? *)', LAMBDA_EXPIRATION_ARN)