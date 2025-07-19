import boto3
import time
from app.config import Config  # Load AWS details from config.py

logs_client = boto3.client(
    'logs',
    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
    region_name=Config.AWS_REGION
)

LOG_GROUP = 'foodosis-logs'  # Log group name (create in CloudWatch console if needed)
LOG_STREAM = 'app-stream'  # Log stream name

def put_log_event(message):
    try:
        logs_client.put_log_events(
            logGroupName=LOG_GROUP,
            logStreamName=LOG_STREAM,
            logEvents=[{'timestamp': int(time.time() * 1000), 'message': message}]
        )
    except logs_client.exceptions.ResourceNotFoundException:
        # Create log group/stream if not exists
        logs_client.create_log_group(logGroupName=LOG_GROUP)
        logs_client.create_log_stream(logGroupName=LOG_GROUP, logStreamName=LOG_STREAM)
        logs_client.put_log_events(
            logGroupName=LOG_GROUP,
            logStreamName=LOG_STREAM,
            logEvents=[{'timestamp': int(time.time() * 1000), 'message': message}]
        )