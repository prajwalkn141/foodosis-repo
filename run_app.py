import os
import webbrowser
import time
from dotenv import load_dotenv

load_dotenv()
if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SESSION_TOKEN'):
    print("Error: AWS credentials missing or invalid in .env. Please update and restart.")
    exit(1)

os.environ['FLASK_APP'] = 'app/__init__.py'
os.environ['FLASK_DEBUG'] = '1'

os.system('flask run &')
time.sleep(2)
webbrowser.open('http://127.0.0.1:5000/login')