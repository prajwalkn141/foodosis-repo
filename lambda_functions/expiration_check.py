import os
import json
import boto3
from datetime import datetime, timedelta

# No need for special path manipulation

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

    # For now, let's simplify and test just the SNS functionality
    # We'll add the database connection later
    
    # Test notification
    if event.get('test', False):
        print("Test mode - sending test notification")
        try:
            subject = "Foodosis Test Notification"
            message = "This is a test notification from Foodosis Lambda function. If you receive this, your Lambda-SNS integration is working!"
            
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=subject,
                Message=message
            )
            print("Test notification sent successfully")
            return {
                'statusCode': 200,
                'body': json.dumps('Test notification sent successfully.')
            }
        except Exception as e:
            print(f"Error sending test notification: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps(f'Error sending test notification: {str(e)}')
            }
    
    # Import RDS utils here to avoid module import issues
    try:
        from foodosis_aws_utils import rds_utils
    except ImportError as e:
        print(f"Warning: Could not import rds_utils: {e}")
        print("Attempting direct database connection...")
        
        # Direct database connection for Lambda
        import mysql.connector
        
        def get_connection():
            return mysql.connector.connect(
                host=os.getenv('RDS_HOST'),
                port=int(os.getenv('RDS_PORT', '3306')),
                database=os.getenv('RDS_DB'),
                user=os.getenv('RDS_USER'),
                password=os.getenv('RDS_PASSWORD')
            )
        
        def get_items():
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM Inventory")
            items = cur.fetchall()
            cur.close()
            conn.close()
            return items
        
        def get_expiring_items():
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id, name, expiration_date FROM Inventory WHERE expiration_date IS NOT NULL AND expiration_date < DATE_ADD(CURDATE(), INTERVAL 7 DAY)")
            items = cur.fetchall()
            cur.close()
            conn.close()
            return items
        
        # Use local functions
        rds_utils = type('obj', (object,), {
            'get_items': get_items,
            'get_expiring_items': get_expiring_items
        })

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
        expiry_date_obj = item.get('expiration_date')
        
        # Handle both datetime and date objects
        if expiry_date_obj:
            if hasattr(expiry_date_obj, 'date'):
                # It's a datetime object
                expiry_date = expiry_date_obj.date()
            else:
                # It's already a date object
                expiry_date = expiry_date_obj
            
            days_until_expiry = (expiry_date - datetime.now().date()).days
            
            if days_until_expiry <= 7:
                expiry_date_str = expiry_date.strftime('%Y-%m-%d')
                
                subject = f"Foodosis Alert: Item '{item_name}' Expiring Soon!"
                message = (
                    f"Dear User,\n\n"
                    f"This is an automated alert from Foodosis regarding your inventory.\n\n"
                    f"The item '{item_name}' (ID: {item_id}) is expiring soon.\n"
                    f"Its expiration date is: {expiry_date_str}.\n"
                    f"Days until expiry: {days_until_expiry}\n\n"
                    f"Please take necessary action to manage your stock.\n\n"
                    f"Thank you,\n"
                    f"Foodosis Inventory Management Team"
                )

                print(f"Publishing SNS message for item: {item_name} (ID: {item_id}, Expiry: {expiry_date_str})")
                try:
                    sns_client.publish(
                        TopicArn=SNS_TOPIC_ARN,
                        Subject=subject,
                        Message=message
                    )
                    print(f"SNS message published successfully for item: {item_name}")
                    notifications_sent += 1
                except Exception as e:
                    print(f"Error publishing SNS message for item {item_name}: {e}")
            else:
                print(f"Item {item_name} (ID: {item_id}) expires in {days_until_expiry} days (not within 7 days).")

    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully processed. Notifications sent: {notifications_sent}.')
    }