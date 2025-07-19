import boto3
from dotenv import load_dotenv
import os
import zipfile
import shutil
import tempfile
import subprocess
import sys

# --- Determine the absolute project root directory ---
_current_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root_dir_absolute = os.path.dirname(_current_script_dir)
# --- End of project root determination ---


load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

lambda_client = boto3.client(
    'lambda',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name=AWS_REGION
)

events_client = boto3.client(
    'events',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name=AWS_REGION
)

# IAM Role ARN for Lambda (use the one from your AWS Learner Lab)
LAMBDA_ROLE_ARN = 'arn:aws:iam::347361551351:role/LabRole'

def zip_lambda_code(lambda_file_name_without_ext):
    """
    Packages the specific Lambda function file, foodosis_aws_utils, and mysql-connector-python
    into a zip file suitable for Lambda deployment.
    """
    temp_dir = tempfile.mkdtemp()
    zip_file_name = f"{lambda_file_name_without_ext}.zip"
    zip_file_path = os.path.join(tempfile.gettempdir(), zip_file_name)

    try:
        lambda_source_file = os.path.join(_project_root_dir_absolute, 'lambda_functions', f'{lambda_file_name_without_ext}.py')
        if not os.path.exists(lambda_source_file):
            raise FileNotFoundError(f"Lambda source file not found: {lambda_source_file}")
        
        shutil.copy(lambda_source_file, os.path.join(temp_dir, f'{lambda_file_name_without_ext}.py'))
        print(f"Copied {lambda_source_file} to {temp_dir}/{lambda_file_name_without_ext}.py")

        aws_utils_source_path = os.path.join(_project_root_dir_absolute, 'foodosis_aws_utils')
        if not os.path.exists(aws_utils_source_path):
            raise FileNotFoundError(f"foodosis_aws_utils directory not found: {aws_utils_source_path}")
        shutil.copytree(aws_utils_source_path, os.path.join(temp_dir, 'foodosis_aws_utils'))
        print(f"Copied {aws_utils_source_path} to {temp_dir}/foodosis_aws_utils")

        app_config_source_path = os.path.join(_project_root_dir_absolute, 'app', 'config.py')
        if not os.path.exists(app_config_source_path):
             print(f"Warning: app/config.py not found at {app_config_source_path}. Ensure RDS env vars are set in Lambda.")
        else:
            os.makedirs(os.path.join(temp_dir, 'app'), exist_ok=True)
            shutil.copy(app_config_source_path, os.path.join(temp_dir, 'app', 'config.py'))
            print(f"Copied {app_config_source_path} to {temp_dir}/app/config.py")

        print(f"Installing mysql-connector-python into {temp_dir}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'mysql-connector-python', '-t', temp_dir])
        print("mysql-connector-python installed successfully.")

        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zf.write(file_path, arcname)
        print(f"Created zip file: {zip_file_path}")

        with open(zip_file_path, 'rb') as f:
            zipped_code = f.read()

        return zipped_code

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")


def create_or_update_lambda_function(lambda_file_name_without_ext, role_arn, env_vars):
    """
    Creates a new Lambda function or updates an existing one.
    """
    function_name = f"foodosis-{lambda_file_name_without_ext.replace('_', '-')}-lambda"
    zipped_code = zip_lambda_code(lambda_file_name_without_ext) 

    handler_name = f'{lambda_file_name_without_ext}.lambda_handler'

    try:
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        
        print(f"Updating existing Lambda function: '{function_name}'...")
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zipped_code,
            Publish=True
        )
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Runtime='python3.12',
            Role=role_arn,
            Handler=handler_name,
            Environment={'Variables': env_vars},
            Timeout=30,
            MemorySize=128
        )
        print(f"Lambda '{function_name}' updated successfully.")
        return response['FunctionArn']

    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"Creating new Lambda function: '{function_name}'...")
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.12',
            Role=role_arn,
            Handler=handler_name,
            Code={'ZipFile': zipped_code},
            Timeout=30,
            MemorySize=128,
            Environment={'Variables': env_vars}
        )
        print(f"Lambda '{function_name}' created: {response['FunctionArn']}")
        return response['FunctionArn']
    except Exception as e:
        print(f"Error creating/updating Lambda '{function_name}': {e}")
        return None

def add_cloudwatch_event_permission(lambda_function_name, lambda_function_arn, rule_name, rule_arn):
    """
    Grants permission for the CloudWatch Event Rule to invoke the Lambda function.
    """
    try:
        lambda_client.add_permission(
            FunctionName=lambda_function_name,
            StatementId=f'{rule_name}-InvokePermission',
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=rule_arn
        )
        print(f"Permission granted for rule '{rule_name}' to invoke Lambda '{lambda_function_name}'.")
    except lambda_client.exceptions.ResourceConflictException:
        print(f"Permission for rule '{rule_name}' to invoke Lambda '{lambda_function_name}' already exists.")
    except Exception as e:
        print(f"Error granting permission for '{lambda_function_name}': {e}")


if __name__ == "__main__":
    rds_env_vars = {
        'RDS_HOST': os.getenv('RDS_HOST'),
        'RDS_PORT': os.getenv('RDS_PORT'),
        'RDS_DB': os.getenv('RDS_DB'),
        'RDS_USER': os.getenv('RDS_USER'),
        'RDS_PASSWORD': os.getenv('RDS_PASSWORD'),
        # Removed 'AWS_REGION': AWS_REGION from here
    }

    # --- Deploy Expiry Check Lambda ---
    expiry_lambda_file_name = 'expiration_check'
    expiry_lambda_name = f"foodosis-{expiry_lambda_file_name.replace('_', '-')}-lambda"
    expiry_sns_topic_arn = os.getenv('SNS_TOPIC_ARN')
    
    if not expiry_sns_topic_arn:
        print("Error: SNS_TOPIC_ARN is not set in your .env file. Cannot deploy expiry_check Lambda.")
    else:
        expiry_env_vars = {**rds_env_vars, 'SNS_TOPIC_ARN': expiry_sns_topic_arn}
        print(f"\nDeploying {expiry_lambda_name}...")
        expiry_lambda_arn = create_or_update_lambda_function(
            expiry_lambda_file_name,
            LAMBDA_ROLE_ARN,
            expiry_env_vars
        )

        if expiry_lambda_arn:
            expiry_rule_name = 'daily_expiration_check'
            try:
                rule_response = events_client.describe_rule(Name=expiry_rule_name)
                expiry_rule_arn = rule_response['Arn']
                add_cloudwatch_event_permission(
                    expiry_lambda_name,
                    expiry_lambda_arn,
                    expiry_rule_name,
                    expiry_rule_arn
                )
            except events_client.exceptions.ResourceNotFoundException:
                print(f"CloudWatch Rule '{expiry_rule_name}' not found. Please ensure it's created.")
            except Exception as e:
                print(f"Error getting ARN for rule '{expiry_rule_name}': {e}")


    # --- Deploy Stock Check Lambda ---
    stock_lambda_file_name = 'stock_check'
    stock_lambda_name = f"foodosis-{stock_lambda_file_name.replace('_', '-')}-lambda"
    stock_env_vars = rds_env_vars

    print(f"\nDeploying {stock_lambda_name}...")
    stock_lambda_arn = create_or_update_lambda_function(
        stock_lambda_file_name,
        LAMBDA_ROLE_ARN,
        stock_env_vars
    )

    if stock_lambda_arn:
        stock_rule_name = 'daily_stock_check'
        try:
            rule_response = events_client.describe_rule(Name=stock_rule_name)
            stock_rule_arn = rule_response['Arn']
            add_cloudwatch_event_permission(
                stock_lambda_name,
                stock_lambda_arn,
                stock_rule_name,
                stock_rule_arn
            )
        except events_client.exceptions.ResourceNotFoundException:
            print(f"CloudWatch Rule '{stock_rule_name}' not found. Please ensure it's created.")
        except Exception as e:
            print(f"Error getting ARN for rule '{stock_rule_name}': {e}")
