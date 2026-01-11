"""
MongoDB database connection and initialization.
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config.settings import Config
from utils import logger

# Global database client and connection
_client = None
_db = None


def get_database():
    """
    Get or create MongoDB database connection.
    
    Returns:
        Database instance
    """
    global _client, _db
    
    if _db is not None:
        return _db
    
    try:
        # Create MongoDB client
        _client = MongoClient(
            Config.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000
        )
        
        # Test connection
        _client.admin.command('ping')
        
        # Get database
        _db = _client[Config.MONGODB_DB_NAME]
        
        logger.info(f"Connected to MongoDB database: {Config.MONGODB_DB_NAME}")
        
        # Create indexes
        _create_indexes()
        
        return _db
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise


def _create_indexes():
    """Create database indexes for better query performance."""
    db = _db
    
    # Simulations collection indexes
    simulations = db.simulations
    simulations.create_index("timestamp")
    simulations.create_index("crash_configuration")
    simulations.create_index("occupant_gender")
    simulations.create_index([("timestamp", -1)])  # Descending for recent-first queries


def close_database():
    """Close MongoDB connection."""
    global _client, _db
    
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")
