import os
import json
import boto3
from datetime import datetime, timedelta

# Assuming foodosis_aws_utils is available in the Lambda deployment package
from foodosis_aws_utils import rds_utils

# Initialize SNS client
sns_client = boto3.client('sns', region_name=os.getenv('AWS_REGION', 'us-east-1'))

# SNS_TOPIC_ARN should be set as an environment variable in your Lambda function configuration
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN')

def lambda_handler(event, context):
    """
    Lambda function handler to check for expiring items and send SNS notifications.
    Can be triggered by CloudWatch Schedule or direct invocation with item_id.
    """
    print("Expiry Check Lambda triggered.")
    print(f"Received event: {json.dumps(event)}")

    if not SNS_TOPIC_ARN:
        print("Error: SNS_TOPIC_ARN environment variable not set. Cannot send notifications.")
        return {
            'statusCode': 500,
            'body': json.dumps('SNS Topic ARN not configured in Lambda environment variables.')
        }

    items_to_check = []
    
    # Determine if it's a direct invocation for a specific item or a scheduled run
    if 'item_id' in event:
        # This is a direct invocation from Flask for a specific item
        item_id = event['item_id']
        print(f"Direct invocation for item ID: {item_id}")
        try:
            all_items = rds_utils.get_items()
            specific_item = next((i for i in all_items if i['id'] == item_id), None)
            if specific_item:
                items_to_check.append(specific_item)
                print(f"Found specific item: {specific_item.get('name')}")
            else:
                print(f"Item with ID {item_id} not found in database.")
                return {
                    'statusCode': 404,
                    'body': json.dumps(f'Item with ID {item_id} not found.')
                }
        except Exception as e:
            print(f"Error fetching specific item from RDS: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps(f'Error fetching specific item: {str(e)}')
            }
    else:
        # This is likely a scheduled invocation (CloudWatch Event)
        print("Scheduled invocation. Checking all expiring items.")
        try:
            items_to_check = rds_utils.get_expiring_items()
        except Exception as e:
            print(f"Error fetching expiring items from RDS: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps(f'Error fetching expiring items: {str(e)}')
            }

    if not items_to_check:
        print("No items found matching the criteria. No notifications sent.")
        return {
            'statusCode': 200,
            'body': json.dumps('No expiring items to notify.')
        }

    print(f"Found {len(items_to_check)} item(s) to check for notification.")

    notifications_sent = 0
    for item in items_to_check:
        item_id = item.get('id', 'N/A')
        item_name = item.get('name', 'Unknown Item')
        expiry_date_str = item.get('expiration_date')
        
        if expiry_date_str:
            try:
                expiry_date_obj = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                creation_date = datetime.now().date()  # Approximate creation date
                days_until_expiry = (expiry_date_obj - creation_date).days
                
                # Prioritize event-provided days_until_expiry for direct invocation
                if 'days_until_expiry' in event:
                    event_days = event.get('days_until_expiry')
                    if isinstance(event_days, (int, float)) and 0 <= event_days <= 365:  # Validate range
                        days_until_expiry = event_days
                        print(f"Using event-provided days_until_expiry: {days_until_expiry}")
                    else:
                        print(f"Invalid days_until_expiry from event: {event_days}, falling back to calculated value.")

                if days_until_expiry <= 7:  # Threshold of 7 days inclusive
                    subject = f"Foodosis Alert: Item '{item_name}' Expiring Soon!"
                    message = (
                        f"Dear User,\n\n"
                        f"This is an automated alert from Foodosis regarding your inventory.\n\n"
                        f"The item '{item_name}' (ID: {item_id}) is expiring soon.\n"
                        f"Expiration date: {expiry_date_str}.\n"
                        f"Days until expiry: {days_until_expiry}.\n\n"
                        f"Please take necessary action to manage your stock.\n\n"
                        f"Thank you,\n"
                        f"Foodosis Inventory Management Team"
                    )

                    print(f"Publishing SNS message for item: {item_name} (ID: {item_id}, Expiry: {expiry_date_str}, Days: {days_until_expiry})")
                    try:
                        response = sns_client.publish(
                            TopicArn=SNS_TOPIC_ARN,
                            Subject=subject,
                            Message=message
                        )
                        print(f"SNS message published successfully for item: {item_name}, Response: {response}")
                        notifications_sent += 1
                    except Exception as e:
                        print(f"Error publishing SNS message for item {item_name}: {e}")
                        # Log detailed error for debugging
                        if "AccessDenied" in str(e):
                            print("AccessDenied: Check Lambda execution role permissions for SNS.")
                        elif "InvalidParameterValue" in str(e):
                            print("InvalidParameterValue: Verify SNS_TOPIC_ARN and message content.")
                else:
                    print(f"Item {item_name} (ID: {item_id}) does not meet the immediate expiry criteria (within 7 days). Days until expiry: {days_until_expiry}")
            except ValueError as ve:
                print(f"Error parsing expiry date for item {item_name}: {ve}")
            except Exception as e:
                print(f"Unexpected error processing item {item_name}: {e}")
        else:
            print(f"Item {item_name} (ID: {item_id}) has no expiration date.")

    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully processed. Notifications sent: {notifications_sent}.')
    }