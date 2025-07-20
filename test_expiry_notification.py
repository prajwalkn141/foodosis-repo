# test_expiry_notification.py
# Save this in your project root and run it to test the notification system

from dotenv import load_dotenv
import os

# Load environment variables FIRST before any other imports
load_dotenv()

import boto3
import json
from datetime import datetime, timedelta

# Test 1: Direct Lambda Invocation Test
def test_lambda_directly():
    """Test if your Lambda function works by invoking it directly"""
    
    print("=== Testing Lambda Function Directly ===")
    
    # Initialize Lambda client
    lambda_client = boto3.client(
        'lambda',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
    
    # First, let's add a test item to the database that expires soon
    from foodosis_aws_utils import rds_utils
    
    # Calculate expiration date (3 days from now)
    expiration_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    
    print(f"Adding test item with expiration date: {expiration_date}")
    
    # Add test item
    item_id = rds_utils.add_item(
        name="Test Expiring Item",
        quantity=50,
        unit="kg",
        expiration_date=expiration_date,
        s3_file_key=None
    )
    
    print(f"Test item added with ID: {item_id}")
    
    # Now invoke Lambda with this specific item
    payload = {"item_id": item_id}
    
    try:
        print(f"Invoking Lambda function with payload: {payload}")
        
        response = lambda_client.invoke(
            FunctionName='foodosis-expiration-check-lambda',
            InvocationType='RequestResponse',  # Synchronous for testing
            Payload=json.dumps(payload)
        )
        
        # Read the response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"Lambda Status Code: {response['StatusCode']}")
        print(f"Lambda Response: {response_payload}")
        
        if response['StatusCode'] == 200:
            print("✅ Lambda invocation successful!")
            print("Check your email for the notification!")
        else:
            print("❌ Lambda invocation failed!")
            
    except Exception as e:
        print(f"❌ Error invoking Lambda: {e}")
        print("Make sure your Lambda function is deployed correctly")

# Test 2: Test SNS Directly
def test_sns_directly():
    """Test if SNS is working by sending a test message"""
    
    print("\n=== Testing SNS Directly ===")
    
    sns_client = boto3.client(
        'sns',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
    
    topic_arn = os.getenv('SNS_TOPIC_ARN')
    
    if not topic_arn:
        print("❌ SNS_TOPIC_ARN not found in .env file!")
        return
    
    try:
        response = sns_client.publish(
            TopicArn=topic_arn,
            Subject='Foodosis Test Notification',
            Message='This is a test message from Foodosis to verify SNS is working correctly.'
        )
        
        print(f"✅ SNS test message sent successfully!")
        print(f"Message ID: {response['MessageId']}")
        print("Check your email for the test message!")
        
    except Exception as e:
        print(f"❌ Error sending SNS message: {e}")
        print("Make sure your SNS topic is set up and email is confirmed")

# Test 3: Test the complete flow through the web app
def test_web_app_flow():
    """Instructions for testing through the web interface"""
    
    print("\n=== Testing Through Web Interface ===")
    print("1. Start your Flask app: python run_app.py")
    print("2. Go to http://127.0.0.1:5000/login")
    print("3. Login with your credentials")
    print("4. Click 'Add Item'")
    print("5. Fill in the form with:")
    print("   - Name: Test Product")
    print("   - Quantity: 100")
    print("   - Unit: kg")
    print(f"   - Expiration Date: {(datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')} (5 days from now)")
    print("6. Click 'Add Item'")
    print("7. You should see a flash message about the expiry check being triggered")
    print("8. Check your email for the notification!")

if __name__ == "__main__":
    print("Foodosis Expiry Notification Test Suite")
    print("======================================")
    
    # Run all tests
    test_sns_directly()
    test_lambda_directly()
    test_web_app_flow()
    
    print("\n✅ All tests completed! Check your email for notifications.")