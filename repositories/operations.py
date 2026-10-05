"""Repository for operations collection.

Implements CRUD operations for service operation metadata:
- create_operation
- get_operation
- list_operations (optionally by service)
- update_operation
- delete_operation
"""

from typing import Any, Dict, List, Optional
from db.connection import get_database


def get_operations_collection():
    return get_database().operations


def create_operation(
    service_name: str,
    operation_name: str,
    operation_type: str = "http",
    active: bool = True,
) -> Dict[str, str]:
    """Register a new operation for a service."""
    col = get_operations_collection()
    doc = {
        "service_name": service_name,
        "operation_name": operation_name,
        "operation_type": operation_type,
        "active": active,
    }
    col.insert_one(doc)
    return {"service_name": service_name, "operation_name": operation_name}


def get_operation(service_name: str, operation_name: str) -> Optional[Dict[str, Any]]:
    """Retrieve operation metadata by service and operation name."""
    col = get_operations_collection()
    return col.find_one(
        {"service_name": service_name, "operation_name": operation_name},
        {"_id": 0},
    )


def list_operations(service_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """List registered operations, optionally filtered by service."""
    col = get_operations_collection()
    query = {"service_name": service_name} if service_name else {}
    return list(
        col.find(query, {"_id": 0}).sort([("service_name", 1), ("operation_name", 1)])
    )


def update_operation(
    service_name: str, operation_name: str, update_fields: Dict[str, Any]
) -> bool:
    """Update operation metadata."""
    col = get_operations_collection()
    allowed_keys = {"operation_type", "active"}
    clean_fields = {k: v for k, v in update_fields.items() if k in allowed_keys}
    if not clean_fields:
        return False

    result = col.update_one(
        {"service_name": service_name, "operation_name": operation_name},
        {"$set": clean_fields},
    )
    return result.modified_count > 0


def delete_operation(service_name: str, operation_name: str) -> bool:
    """Delete an operation metadata document."""
    col = get_operations_collection()
    result = col.delete_one(
        {"service_name": service_name, "operation_name": operation_name}
    )
    return result.deleted_count > 0
