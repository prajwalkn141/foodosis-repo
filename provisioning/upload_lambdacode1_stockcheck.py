import boto3
from dotenv import load_dotenv
import os
import zipfile

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

def zip_lambda_code(file_path, zip_name='lambda_code.zip'):
    with zipfile.ZipFile(zip_name, 'w') as zf:
        zf.write(file_path, arcname=os.path.basename(file_path))
    with open(zip_name, 'rb') as f:
        zipped_code = f.read()
    os.remove(zip_name)  # Cleanup ZIP
    return zipped_code

def upload_lambda_code(function_name, file_path):
    zipped_code = zip_lambda_code(file_path)
    try:
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zipped_code
        )
        print(f"Lambda code for '{function_name}' uploaded successfully: {response['LastModified']}")
    except Exception as e:
        print(f"Error uploading Lambda code for '{function_name}': {e}")

if __name__ == "__main__":
    # Upload for stock_check
    upload_lambda_code('stock_check', 'D:\\foodosis\\lambda_functions\\stock_check.py')
    
    # Upload for expiration_check
    upload_lambda_code('expiration_check', 'D:\\foodosis\\lambda_functions\\expiration_check.py')