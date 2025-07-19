import boto3
import json
import time
from foodosis_aws_utils import rds_utils, s3_utils, auth_utils, sns_utils, cloudwatch_utils

# Test RDS (connection and query)
try:
    conn = rds_utils.get_connection()
    conn.close()
    print("RDS connection successful.")
except Exception as e:
    print(f"RDS connection failed: {e}")

# Test S3 (head bucket to check existence)
try:
    s3_utils.s3_client.head_bucket(Bucket='foodosis-files')
    print("S3 connection successful.")
except Exception as e:
    print(f"S3 connection failed: {e}")

# Test SNS (publish test message)
try:
    sns_utils.publish_notification("Test SNS message from Foodosis")
    print("SNS connection successful.")
except Exception as e:
    print(f"SNS connection failed: {e}")

# Test CloudWatch (put test log event)
try:
    cloudwatch_utils.put_log_event("Test log from Foodosis")
    print("CloudWatch connection successful.")
except Exception as e:
    print(f"CloudWatch connection failed: {e}")

# Test Lambda (invoke test call to stock_check; assume Lambda ARN in config if needed)
try:
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    response = lambda_client.invoke(FunctionName='stock_check', Payload=json.dumps({}))
    print("Lambda connection successful if status 200:", response['StatusCode'])
except Exception as e:
    print(f"Lambda connection failed: {e}")