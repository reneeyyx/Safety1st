"""
MongoDB model for simulation results.
Handles saving and retrieving crash simulation data.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from bson import ObjectId
from database import get_database


class SimulationResult:
    """MongoDB model for crash simulation results."""
    
    COLLECTION_NAME = "simulations"
    
    @staticmethod
    def save(
        car_data: Dict[str, Any],
        dummy_data: Dict[str, Any],
        baseline_results: Dict[str, Any],
        gemini_analysis: Optional[Dict[str, Any]] = None,
        scraped_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save a simulation result to MongoDB.
        
        Args:
            car_data: Car/vehicle parameters
            dummy_data: Occupant/dummy parameters
            baseline_results: Physics calculation results
            gemini_analysis: Gemini AI analysis (risk score, confidence, explanation)
            scraped_context: Web scraped safety data
            
        Returns:
            Simulation ID (string)
        """
        db = get_database()
        collection = db[SimulationResult.COLLECTION_NAME]
        
        # Prepare document
        document = {
            "timestamp": datetime.utcnow(),
            
            # Input parameters
            "car_data": car_data,
            "dummy_data": dummy_data,
            
            # Baseline physics results
            "baseline": {
                "risk_score": baseline_results.get("risk_score_0_100", 0),
                "HIC15": baseline_results.get("HIC15", 0),
                "Nij": baseline_results.get("Nij", 0),
                "chest_A3ms_g": baseline_results.get("chest_A3ms_g", 0),
                "thorax_deflection_mm": baseline_results.get("thorax_irtracc_max_deflection_proxy_mm", 0),
                "femur_load_kN": baseline_results.get("femur_load_kN", 0),
                "P_head": baseline_results.get("P_head", 0),
                "P_neck": baseline_results.get("P_neck", 0),
                "P_thorax": baseline_results.get("P_thorax_AIS3plus", 0),
                "P_femur": baseline_results.get("P_femur", 0),
                "P_baseline": baseline_results.get("P_baseline", 0),
                "delta_v_mps": baseline_results.get("delta_v_mps", 0),
                "peak_accel_g": baseline_results.get("peak_accel_g", 0)
            },
            
            # AI-enhanced results (if available)
            "gemini_analysis": gemini_analysis if gemini_analysis else None,
            
            # Scraped context (if available)
            "scraped_context": scraped_context if scraped_context else None,
            
            # Quick access fields for filtering/sorting
            "crash_configuration": baseline_results.get("crash_configuration", "unknown"),
            "occupant_gender": baseline_results.get("occupant_gender", "unknown"),
            "is_pregnant": baseline_results.get("is_pregnant", False),
            "final_risk_score": gemini_analysis.get("risk_score", baseline_results.get("risk_score_0_100", 0)) if gemini_analysis else baseline_results.get("risk_score_0_100", 0)
        }
        
        # Insert into database
        result = collection.insert_one(document)
        
        return str(result.inserted_id)
    
    @staticmethod
    def get_all(limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve all simulations, sorted by most recent first.
        
        Args:
            limit: Maximum number of results to return
            skip: Number of results to skip (for pagination)
            
        Returns:
            List of simulation documents
        """
        db = get_database()
        collection = db[SimulationResult.COLLECTION_NAME]
        
        cursor = collection.find().sort("timestamp", -1).skip(skip).limit(limit)
        
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
            results.append(doc)
        
        return results
    
    @staticmethod
    def get_by_id(simulation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single simulation by ID.
        
        Args:
            simulation_id: MongoDB ObjectId as string
            
        Returns:
            Simulation document or None if not found
        """
        db = get_database()
        collection = db[SimulationResult.COLLECTION_NAME]
        
        try:
            doc = collection.find_one({"_id": ObjectId(simulation_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
        except Exception:
            return None
    
    @staticmethod
    def delete_by_id(simulation_id: str) -> bool:
        """
        Delete a simulation by ID.
        
        Args:
            simulation_id: MongoDB ObjectId as string
            
        Returns:
            True if deleted, False otherwise
        """
        db = get_database()
        collection = db[SimulationResult.COLLECTION_NAME]
        
        try:
            result = collection.delete_one({"_id": ObjectId(simulation_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    @staticmethod
    def get_by_filters(
        crash_type: Optional[str] = None,
        gender: Optional[str] = None,
        pregnant: Optional[bool] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieve simulations with filters.
        
        Args:
            crash_type: Filter by crash configuration (frontal/side/rear)
            gender: Filter by occupant gender
            pregnant: Filter by pregnancy status
            limit: Maximum number of results
            
        Returns:
            List of matching simulation documents
        """
        db = get_database()
        collection = db[SimulationResult.COLLECTION_NAME]
        
        # Build query
        query = {}
        if crash_type:
            query["crash_configuration"] = crash_type
        if gender:
            query["occupant_gender"] = gender
        if pregnant is not None:
            query["is_pregnant"] = pregnant
        
        cursor = collection.find(query).sort("timestamp", -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        
        return results
    
    @staticmethod
    def count_all() -> int:
        """Get total count of simulations."""
        db = get_database()
        collection = db[SimulationResult.COLLECTION_NAME]
        return collection.count_documents({})
