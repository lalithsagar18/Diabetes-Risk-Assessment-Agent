import streamlit as st
import bcrypt
import os
from datetime import datetime

def init_session_state():
    """Initialize default values in st.session_state if they are missing."""
    defaults = {
        "authenticated": False,
        "user_id": None,
        "dark_mode": False,
        "login_error": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def hash_password(plain_password: str) -> str:
    """Hash a plain password using bcrypt and return the hashed string.

    The returned value is decoded to UTF-8 for storage in SQLite.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hashed password."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def validate_patient_input(data: dict) -> (bool, str):
    """Validate patient registration form data.
    Returns (is_valid, error_message).
    """
    required_fields = [
        "full_name", "age", "gender", "phone", "email", "address",
        "pregnancies", "glucose", "blood_pressure", "skin_thickness",
        "insulin", "bmi", "diabetes_pedigree"
    ]
    for field in required_fields:
        if field not in data or data[field] in ("", None):
            return False, f"{field.replace('_', ' ').title()} is required."
    try:
        # Numeric validations
        int(data["age"])
        float(data["bmi"])
        float(data["diabetes_pedigree"])
    except ValueError:
        return False, "Numeric fields must contain valid numbers."
    return True, ""

def get_current_timestamp():
    """Return current UTC timestamp string suitable for SQLite DATETIME fields."""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def get_secret(key: str):
    """Retrieve a secret from Streamlit secrets or environment variables.
    Returns None if not found.
    """
    if key in st.secrets:
        return st.secrets[key]
    return os.getenv(key)
