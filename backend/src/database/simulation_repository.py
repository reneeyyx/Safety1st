"""
Repository for managing crash simulation results in MongoDB
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from bson import ObjectId
from .mongodb import mongodb


class SimulationRepository:
    """Repository for CRUD operations on simulation results"""

    def __init__(self):
        self.db = mongodb.get_database()
        self.collection = self.db['simulations']

    def save_simulation(self, simulation_data: Dict[str, Any]) -> str:
        """
        Save a simulation result to the database

        Args:
            simulation_data: Dictionary containing simulation input and output data

        Returns:
            str: The ID of the inserted document
        """
        # Add timestamp
        simulation_data['created_at'] = datetime.utcnow()

        # Insert into database
        result = self.collection.insert_one(simulation_data)

        return str(result.inserted_id)

    def get_all_simulations(self, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve all simulations, sorted by most recent first

        Args:
            limit: Maximum number of results to return
            skip: Number of results to skip (for pagination)

        Returns:
            List of simulation documents
        """
        simulations = list(
            self.collection.find()
            .sort('created_at', -1)
            .skip(skip)
            .limit(limit)
        )

        # Convert ObjectId to string for JSON serialization
        for sim in simulations:
            sim['_id'] = str(sim['_id'])
            # Convert datetime to ISO format string
            if 'created_at' in sim:
                sim['created_at'] = sim['created_at'].isoformat()

        return simulations

    def get_simulation_by_id(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific simulation by ID

        Args:
            simulation_id: The ID of the simulation

        Returns:
            Simulation document or None if not found
        """
        try:
            simulation = self.collection.find_one({'_id': ObjectId(simulation_id)})

            if simulation:
                simulation['_id'] = str(simulation['_id'])
                if 'created_at' in simulation:
                    simulation['created_at'] = simulation['created_at'].isoformat()

            return simulation
        except Exception:
            return None

    def delete_simulation(self, simulation_id: str) -> bool:
        """
        Delete a simulation by ID

        Args:
            simulation_id: The ID of the simulation to delete

        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            result = self.collection.delete_one({'_id': ObjectId(simulation_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    def get_count(self) -> int:
        """
        Get the total number of simulations in the database

        Returns:
            int: Total count of simulations
        """
        return self.collection.count_documents({})


# Singleton instance
simulation_repo = SimulationRepository()
