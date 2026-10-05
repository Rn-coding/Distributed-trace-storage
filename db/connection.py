from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import Config

_client = None


def get_client(uri=None):
    """Retrieve or create a singleton MongoClient instance."""
    global _client
    if _client is None:
        target_uri = uri or Config.MONGO_URI
        _client = MongoClient(target_uri, serverSelectionTimeoutMS=5000)
    return _client


def get_database(db_name=None):
    """Return the configured MongoDB database."""
    client = get_client()
    target_db = db_name or Config.MONGO_DB
    return client[target_db]


def check_connection():
    """Verify MongoDB connectivity by executing ping."""
    try:
        db = get_database()
        result = db.command("ping")
        return {"status": "connected", "ping": result}
    except (ConnectionFailure, ServerSelectionTimeoutError) as err:
        return {"status": "error", "message": str(err)}


def close_connection():
    """Close the active MongoClient connection."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
