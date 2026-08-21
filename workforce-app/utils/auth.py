"""
Minimal but real auth: users are stored in the `users` collection with
bcrypt-hashed passwords. Session state holds the logged-in user + role.
Roles: "Admin", "Manager", "Employee"
"""

import bcrypt
import streamlit as st
from utils.db import get_db


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def login(username: str, password: str) -> bool:
    db = get_db()
    user = db.users.find_one({"username": username})
    if not user or not verify_password(password, user["password_hash"]):
        return False
    st.session_state["user"] = {
        "username": user["username"],
        "role": user["role"],  # Admin / Manager / Employee
        "employee_id": user.get("employee_id"),
        "name": user.get("name", username),
    }
    return True


def logout():
    st.session_state.pop("user", None)


def current_user():
    return st.session_state.get("user")


def require_login():
    """Call at the top of every page. Stops rendering if not logged in."""
    if "user" not in st.session_state:
        st.warning("Please log in from the Home page first.")
        st.stop()
    return st.session_state["user"]


def require_role(*allowed_roles):
    """Call at the top of a page to restrict it to certain roles."""
    user = require_login()
    if user["role"] not in allowed_roles:
        st.error(f"Access denied. This page is restricted to: {', '.join(allowed_roles)}")
        st.stop()
    return user
