import boto3
from dotenv import load_dotenv
import os
import json

def invoke_lambda(function_name, payload, region='us-east-1'):
    """
    Invoke a Lambda function with fresh credentials loaded from .env.
    
    Args:
        function_name (str): Name of the Lambda function to invoke.
        payload (dict): Data to send to the Lambda function.
        region (str): AWS region (default: 'us-east-1').
    
    Returns:
        dict: Response from Lambda invocation.
    
    Raises:
        ValueError: If AWS credentials are missing from .env.
        Exception: If Lambda invocation fails.
    """
    # Load fresh credentials from .env
    load_dotenv()
    fresh_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    fresh_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    fresh_session_token = os.getenv('AWS_SESSION_TOKEN')

    if not all([fresh_access_key, fresh_secret_key, fresh_session_token]):
        raise ValueError("Missing AWS credentials in .env")

    # Initialize Lambda client with fresh credentials
    lambda_client = boto3.client(
        'lambda',
        aws_access_key_id=fresh_access_key,
        aws_secret_access_key=fresh_secret_key,
        aws_session_token=fresh_session_token,
        region_name=region
    )

    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(payload)
        )
        return response
    except Exception as e:
        raise Exception(f"Failed to invoke Lambda {function_name}: {str(e)}")