"""
MongoDB database connection and configuration
"""
import os
from pymongo import MongoClient
from pymongo.database import Database
from typing import Optional

class MongoDB:
    _instance: Optional['MongoDB'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance

    def connect(self, connection_string: str = None, database_name: str = "safety1st"):
        """
        Connect to MongoDB

        Args:
            connection_string: MongoDB connection string (defaults to env variable)
            database_name: Name of the database to use
        """
        if self._client is None:
            # Get connection string from environment or use default
            conn_str = connection_string or os.getenv(
                'MONGODB_URI',
                'mongodb://localhost:27017/'
            )

            self._client = MongoClient(conn_str)
            self._db = self._client[database_name]

            print(f"✓ Connected to MongoDB database: {database_name}")

        return self._db

    def get_database(self) -> Database:
        """Get the database instance"""
        if self._db is None:
            self.connect()
        return self._db

    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            print("✓ MongoDB connection closed")

# Singleton instance
mongodb = MongoDB()
