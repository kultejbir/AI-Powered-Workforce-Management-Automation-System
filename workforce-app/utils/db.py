"""
Central MongoDB connection helper.
Reads MONGODB_URI / DB_NAME from Streamlit secrets (or environment
variables as a fallback so it also works outside Streamlit Cloud).
"""

import os
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ServerSelectionTimeoutError


def _get_setting(key: str, default: str = "") -> str:
    # st.secrets works locally (via .streamlit/secrets.toml) and on
    # Streamlit Community Cloud (via the Secrets UI). os.environ is a
    # fallback for other hosts (Azure App Service, Docker, etc.)
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


@st.cache_resource(show_spinner=False)
def get_client() -> MongoClient:
    uri = _get_setting("MONGODB_URI")
    if not uri:
        raise RuntimeError(
            "MONGODB_URI is not set. Add it to .streamlit/secrets.toml "
            "locally, or to your app's Secrets in Streamlit Cloud."
        )
    return MongoClient(uri, serverSelectionTimeoutMS=8000)


def get_db():
    client = get_client()
    db_name = _get_setting("DB_NAME", "workforce_db")
    return client[db_name]


def check_connection() -> tuple[bool, str]:
    """Returns (ok, message) — used to show a friendly banner in the app."""
    try:
        get_client().admin.command("ping")
        return True, "Connected to MongoDB"
    except (ConfigurationError, ServerSelectionTimeoutError) as e:
        return False, f"Could not reach MongoDB: {e}"
    except RuntimeError as e:
        return False, str(e)
    except Exception as e:  # noqa: BLE001
        return False, f"Unexpected DB error: {e}"
