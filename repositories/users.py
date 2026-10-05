"""Repository for users collection.

Provides user management and password authentication:
- create_user (hashes password with werkzeug.security)
- get_user_by_username
- verify_user_credentials
- list_users
"""

from typing import Any, Dict, List, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from db.connection import get_database


def get_users_collection():
    return get_database().users


def create_user(
    username: str,
    password: str,
    role: str = "viewer",
    active: bool = True,
) -> str:
    """Create a new user account with hashed password."""
    col = get_users_collection()
    doc = {
        "username": username,
        "password_hash": generate_password_hash(password),
        "role": role,
        "active": active,
    }
    col.insert_one(doc)
    return username


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Retrieve user document by username."""
    col = get_users_collection()
    return col.find_one({"username": username})


def verify_user_credentials(
    username: str, password: str
) -> Optional[Dict[str, Any]]:
    """Verify username and password. Returns user dict (without hash) on success, else None."""
    user = get_user_by_username(username)
    if not user or not user.get("active", False):
        return None
    if check_password_hash(user["password_hash"], password):
        return {
            "username": user["username"],
            "role": user.get("role", "viewer"),
        }
    return None


def list_users() -> List[Dict[str, Any]]:
    """List all users without exposing password hash."""
    col = get_users_collection()
    return list(col.find({}, {"_id": 0, "password_hash": 0}))
