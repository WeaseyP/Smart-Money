"""
Centralized configuration module.

This module loads environment variables from a .env file using python-dotenv
and exposes them as Python constants for use throughout the application.
"""

import os
from dotenv import load_dotenv

# This line looks for a .env file in the project's root directory and loads its content
# into the environment variables.
load_dotenv()

# --- API Configuration ---
# Fetch the API key from the environment variables.
# os.getenv() returns None if the variable is not found.
API_KEY = os.getenv("API_KEY")

# --- Database Configuration ---
# Fetch all the database connection details from the environment variables.
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


# --- Validation (Optional but Recommended) ---
# It's good practice to check if critical variables have been set.
# This helps catch configuration errors early when the application starts.
if not API_KEY:
    raise ValueError("CRITICAL: API_KEY is not set in the .env file.")

if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
    raise ValueError("CRITICAL: One or more database environment variables are missing in the .env file.")
