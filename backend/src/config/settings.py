"""
Safety1st application configuration.
Loads settings from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Flask application configuration class."""

    # Flask Configuration
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-!!!!')

    # API Configuration
    API_VERSION = 'v1'
    API_TITLE = 'Safety1st Crash Risk Calculator API'

    # CORS Configuration
    CORS_ORIGINS = os.getenv(
        'CORS_ORIGINS',
        'http://localhost:3000,http://localhost:5173,http://localhost:5174'
    ).split(',')

    # Gemini AI Configuration (for future integration)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-pro')

    # Calculation Settings
    MAX_IMPACT_SPEED_KMH = float(os.getenv('MAX_IMPACT_SPEED_KMH', '200'))
    MIN_OCCUPANT_MASS_KG = float(os.getenv('MIN_OCCUPANT_MASS_KG', '40'))
    MAX_OCCUPANT_MASS_KG = float(os.getenv('MAX_OCCUPANT_MASS_KG', '150'))

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @staticmethod
    def validate():
        """
        Validate configuration settings.
        Raises ValueError if required settings are missing or invalid.
        """
        if Config.DEBUG and Config.SECRET_KEY == 'dev-secret-key-change-in-production-!!!!':
            print("⚠️  WARNING: Using default SECRET_KEY in production is unsafe!")

        if not Config.GEMINI_API_KEY and not Config.DEBUG:
            print("⚠️  WARNING: GEMINI_API_KEY not set - Gemini analysis will not work")


# Validate on import
Config.validate()
