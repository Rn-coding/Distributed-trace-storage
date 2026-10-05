"""Repository for services collection.

Implements CRUD operations for microservice metadata catalog:
- create_service
- get_service
- list_services
- update_service
- delete_service
"""

from typing import Any, Dict, List, Optional
from db.connection import get_database


def get_services_collection():
    return get_database().services


def create_service(
    service_name: str,
    team: str = "Engineering",
    environment: str = "production",
    active: bool = True,
) -> str:
    """Register a new service document. Returns service_name."""
    col = get_services_collection()
    doc = {
        "service_name": service_name,
        "team": team,
        "environment": environment,
        "active": active,
    }
    col.insert_one(doc)
    return service_name


def get_service(service_name: str) -> Optional[Dict[str, Any]]:
    """Retrieve service metadata by name."""
    col = get_services_collection()
    return col.find_one({"service_name": service_name}, {"_id": 0})


def list_services(active_only: bool = False) -> List[Dict[str, Any]]:
    """Retrieve registered services list sorted alphabetically."""
    col = get_services_collection()
    query = {"active": True} if active_only else {}
    return list(col.find(query, {"_id": 0}).sort("service_name", 1))


def update_service(service_name: str, update_fields: Dict[str, Any]) -> bool:
    """Update metadata for an existing service."""
    col = get_services_collection()
    allowed_keys = {"team", "environment", "active"}
    clean_fields = {k: v for k, v in update_fields.items() if k in allowed_keys}
    if not clean_fields:
        return False

    result = col.update_one(
        {"service_name": service_name},
        {"$set": clean_fields},
    )
    return result.modified_count > 0


def delete_service(service_name: str) -> bool:
    """Delete a service metadata document."""
    col = get_services_collection()
    result = col.delete_one({"service_name": service_name})
    return result.deleted_count > 0
