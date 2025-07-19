from flask import Flask
from flask_session import Session
from flask_bcrypt import Bcrypt
from app.config import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'  # Simple session storage for login

bcrypt = Bcrypt(app)
Session(app)

from app import routes  # Import routes to register endpoints