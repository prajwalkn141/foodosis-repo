import boto3
from dotenv import load_dotenv
import os
import time

load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

rds_client = boto3.client(
    'rds',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name=AWS_REGION
)

RDS_USER = 'admin'  # Master username
RDS_PASSWORD = 'Pajju009*'  # Replace with your strong password

def create_rds_instance():
    try:
        response = rds_client.create_db_instance(
            DBInstanceIdentifier='foodosis-rds',
            MasterUsername=RDS_USER,
            MasterUserPassword=RDS_PASSWORD,
            DBInstanceClass='db.t3.micro',  # Free tier
            Engine='mysql',  # MySQL as preferred
            AllocatedStorage=20,  # Minimum GP2 storage (free tier)
            PubliclyAccessible=True,  # For Workbench access
            MultiAZ=False,  # No HA to save costs
            BackupRetentionPeriod=0,  # No backups
            StorageType='gp2',  # General purpose SSD
            EnablePerformanceInsights=False  # Disabled to avoid costs
        )
        print("Creating RDS MySQL instance... Waiting 5-10 min for availability.")
        waiter = rds_client.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier='foodosis-rds', WaiterConfig={'Delay': 30, 'MaxAttempts': 60})
        endpoint = response['DBInstance']['Endpoint']['Address']
        print(f"RDS instance created successfully. Endpoint: {endpoint}")
        print("Update .env with RDS_HOST=" + endpoint)
        return endpoint
    except Exception as e:
        print(f"Error creating RDS instance: {e}")
        return None

if __name__ == "__main__":
    create_rds_instance()