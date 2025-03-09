from decouple import config
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    API_KEY = config('API_KEY')
    API_SECRET = config('API_SECRET')
    REDIRECT_URI = config('REDIRECT_URI')
    API_VERSION = config('API_VERSION')
    SCOPES = config('SCOPES', default='read_orders').split(',')
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, '..', 'mock_orders.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False