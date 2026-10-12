import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'creatora-dev-super-secret-key-change-in-prod-2025')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configurations
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB max file size
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'docx', 'zip'}
    
    # Session security
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # AI service configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    AI_FALLBACK_MODE = os.environ.get('AI_FALLBACK_MODE', 'true').lower() == 'true'
    LOW_COST_MODE = os.environ.get('LOW_COST_MODE', 'true').lower() == 'true'
    AI_DAILY_LIMIT_PER_USER = int(os.environ.get('AI_DAILY_LIMIT_PER_USER', '50'))

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
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'creatora.db')}")
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'creatora.db')}")
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
