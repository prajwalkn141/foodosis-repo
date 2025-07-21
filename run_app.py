import os
import webbrowser
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# For AWS Learner Lab, we'll skip the credential check since they're hardcoded in deployment
# if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SESSION_TOKEN'):
#     print("Error: AWS credentials missing or invalid in .env. Please update and restart.")
#     exit(1)

# Print loaded credentials for debugging (remove in production)
print("Starting Foodosis application...")
print(f"AWS_ACCESS_KEY_ID: {os.getenv('AWS_ACCESS_KEY_ID', 'Not set')[:10]}...")
print(f"RDS_HOST: {os.getenv('RDS_HOST', 'Not set')}")
print(f"S3_BUCKET: {os.getenv('S3_BUCKET', 'Not set')}")

os.environ['FLASK_APP'] = 'app/__init__.py'
os.environ['FLASK_DEBUG'] = '1'

# Don't open browser in production/server environment
# os.system('flask run &')
# time.sleep(2)
# webbrowser.open('http://127.0.0.1:5000/login')

# For server deployment, just run Flask
if __name__ == '__main__':
    from app import app
    app.run(host='0.0.0.0', port=5000, debug=False)