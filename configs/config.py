"""Module for configuration application file"""

# Natives
import os
from pathlib import Path

# Third parties
from dotenv import load_dotenv

# Retrieve the environment set in docker-compose environment variable
environment = os.getenv("ENVIRONMENT", "development")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")

base_dir = Path(__file__).resolve().parent.parent
load_dotenv(
    base_dir / ".env"
    if environment.lower() == "production"
    # For local execution using JetBrains. It should be improved when dev stages are defined.
    else base_dir / "docker" / "local" / "prod" / ".env"
)

""" Firestore settings
"""
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GCP_PROJECT_ID = os.getenv("PROJECT_ID")
