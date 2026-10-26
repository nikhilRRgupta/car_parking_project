import os
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(basedir, '.env'))


def get_database_uri():
    """
    Returns MySQL database URI if accessible, otherwise falls back gracefully
    to SQLite if ENABLE_SQLITE_FALLBACK is enabled.
    """
    mysql_uri = os.getenv('DATABASE_URL', 'mysql+pymysql://root:password@localhost:3306/smart_parking_db')
    sqlite_fallback_enabled = os.getenv('ENABLE_SQLITE_FALLBACK', 'True').lower() in ('true', '1', 'yes')
    sqlite_path = os.path.join(basedir, 'smart_parking_local.db')
    sqlite_uri = f"sqlite:///{sqlite_path}"

    if not sqlite_fallback_enabled:
        return mysql_uri

    # Test MySQL connection quickly
    try:
        from sqlalchemy import create_engine
        engine = create_engine(mysql_uri, connect_args={"connect_timeout": 2})
        with engine.connect():
            pass
        return mysql_uri
    except Exception:
        # Fall back to SQLite for instant local zero-friction execution
        return sqlite_uri


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'smart-parking-default-secret-key-2026')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    
    # Business Logic
    RESERVATION_EXPIRY_MINUTES = int(os.getenv('RESERVATION_EXPIRY_MINUTES', 10))
    DEFAULT_BASE_HOURS = int(os.getenv('DEFAULT_BASE_HOURS', 4))
    DEFAULT_BASE_RATE = float(os.getenv('DEFAULT_BASE_RATE', 50.00))
    DEFAULT_HOURLY_RATE = float(os.getenv('DEFAULT_HOURLY_RATE', 20.00))
    GRACE_PERIOD_MINUTES = int(os.getenv('GRACE_PERIOD_MINUTES', 15))
    
    # Barrier & Sandbox
    PAYMENT_SANDBOX_MODE = os.getenv('PAYMENT_SANDBOX_MODE', 'True').lower() in ('true', '1', 'yes')
    BARRIER_AUTO_CLOSE_SECONDS = int(os.getenv('BARRIER_AUTO_CLOSE_SECONDS', 6))
    MOCK_UPI_MERCHANT_ID = os.getenv('MOCK_UPI_MERCHANT_ID', 'smartpark@bank')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
