"""
Configuration file for database connection and external services.

This module loads environment variables from a `.env` file using python-dotenv.
We use `find_dotenv()` so the .env file can live either in the project root
or in this `app/config/` folder without changing code.
"""

import os
from dotenv import load_dotenv, find_dotenv

# Load the closest .env file upwards from this directory
load_dotenv(find_dotenv())

# Neon Database connection string
# Expected format (from your Neon dashboard):
#   postgresql://<user>:<password>@<host>/<database>?sslmode=require
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@hostname/database?sslmode=require")

# Validate DATABASE_URL (will be checked at runtime in main.py if needed)
# We don't raise here to allow the app to start and show a proper error message

# Email configuration for notifications (Gmail)
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")

# WhatsApp configuration (using Twilio or similar service)
WHATSAPP_ACCOUNT_SID = os.getenv("WHATSAPP_ACCOUNT_SID", "")
WHATSAPP_AUTH_TOKEN = os.getenv("WHATSAPP_AUTH_TOKEN", "")
WHATSAPP_FROM_NUMBER = os.getenv("WHATSAPP_FROM_NUMBER", "")

