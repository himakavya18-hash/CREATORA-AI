import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def _database_url(default=None):
    url = os.environ.get('SUPABASE_DATABASE_URL') or os.environ.get('DATABASE_URL') or default
    if url and url.startswith('postgres://'):
        return 'postgresql+psycopg://' + url[len('postgres://'):]
    if url and url.startswith('postgresql://'):
        return 'postgresql+psycopg://' + url[len('postgresql://'):]
    return url

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'creatora-dev-super-secret-key-change-in-prod-2025')
    BASE_DIR = BASE_DIR  # expose to current_app.config
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # No Flask upload cap; hosting layers can still impose one.
    MAX_CONTENT_LENGTH = None
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'docx', 'zip'}
    
    # Session security
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # AI service configuration
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'gemma3:1b')
    ADMIN_REGISTRATION_KEY = os.environ.get('ADMIN_REGISTRATION_KEY', 'creatora-admin-2025')
    AI_FALLBACK_MODE = os.environ.get('AI_FALLBACK_MODE', 'true').lower() == 'true'
    LOW_COST_MODE = os.environ.get('LOW_COST_MODE', 'true').lower() == 'true'
    AI_DAILY_LIMIT_PER_USER = int(os.environ.get('AI_DAILY_LIMIT_PER_USER', '0'))
    USD_TO_INR = float(os.environ.get('USD_TO_INR', '96.20'))

    # Matching Weights Configuration (Normalized to 1.0)
    MATCH_WEIGHTS = {
        'skills': 0.25,
        'portfolio': 0.25,
        'specialization': 0.15,
        'tools': 0.10,
        'format': 0.10,
        'budget': 0.10,
        'availability': 0.05
    }

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _database_url(f"sqlite:///{os.path.join(BASE_DIR, 'creatora.db')}")
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _database_url()
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Strict'

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-key'

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
