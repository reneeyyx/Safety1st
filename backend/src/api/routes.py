"""
Flask API routes for Safety1st crash risk calculation.
"""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from typing import Dict, Any
import asyncio

from models.carDataModel import CarDataModel, CarParameters
from models.dummyDataModel import DummyDataModel, DummyDetails
from models.simulationModel import SimulationResult
from modeling.calculator import (
    CrashInputs,
    calculate_baseline_risk
)
from modeling.geminiAPI import (
    analyze_with_gemini,
    format_analysis_for_response
)
from scraper import scrape_safety_data

# Create Flask blueprint
api_blueprint = Blueprint('api', __name__)


def convert_to_scraper_models(car_data: CarDataModel, dummy_data: DummyDataModel) -> tuple:
    """
    Convert API validation models to lightweight scraper models.

    Args:
        car_data: Validated CarDataModel
        dummy_data: Validated DummyDataModel

    Returns:
        Tuple of (CarParameters, DummyDetails) for scraper
    """
    car_params = CarParameters(
        crash_side=car_data.crash_side,
        vehicle_mass=car_data.vehicle_mass_kg,
        crumple_zone_length=car_data.crumple_zone_length_m,
        cabin_rigidity=car_data.cabin_rigidity,
        seatbelt_pretensioner=car_data.seatbelt_pretensioner,
        seatbelt_load_limiter=car_data.seatbelt_load_limiter,
        front_airbags=car_data.front_airbag,
        side_airbags=car_data.side_airbag
    )

    dummy_details = DummyDetails(
        gender=dummy_data.gender,
        seat_position=dummy_data.seat_position,
        pregnant=dummy_data.is_pregnant,
        pelvis_lap_belt_fit=dummy_data.pelvis_lap_belt_fit
    )

    return car_params, dummy_details


def transform_request_to_crash_inputs(car_data: CarDataModel, dummy_data: DummyDataModel) -> CrashInputs:
    """
    Transform validated request models to CrashInputs for calculator.

    Converts user-friendly units to SI units:
    - km/h → m/s
    - cm → m

    Args:
        car_data: Validated car/vehicle data model
        dummy_data: Validated occupant/dummy data model

    Returns:
        CrashInputs object ready for calculator
    """
    return CrashInputs(
        # Crash parameters (from car_data)
        impact_speed=car_data.impact_speed_kmh / 3.6,  # km/h → m/s
        vehicle_mass=car_data.vehicle_mass_kg,
        crash_side=car_data.crash_side,
        coefficient_restitution=0.0,  # Rigid barrier (always 0 for this use case)

        # Occupant (from dummy_data)
        occupant_mass=dummy_data.occupant_mass_kg,
        occupant_height=dummy_data.occupant_height_m,
        gender=dummy_data.gender,
        is_pregnant=dummy_data.is_pregnant,

        # Seating position (from dummy_data)
        seat_distance_from_wheel=dummy_data.seat_distance_from_wheel_cm / 100,  # cm → m
        seat_recline_angle=dummy_data.seat_recline_angle_deg,
        seat_height_relative_to_dash=dummy_data.seat_height_relative_to_dash_cm / 100,  # cm → m
        neck_strength=dummy_data.neck_strength,
        seat_position=dummy_data.seat_position,
        pelvis_lap_belt_fit=dummy_data.pelvis_lap_belt_fit,

        # Restraints (from car_data)
        seatbelt_used=car_data.seatbelt_used,
        seatbelt_pretensioner=car_data.seatbelt_pretensioner,
        seatbelt_load_limiter=car_data.seatbelt_load_limiter,
        front_airbag=car_data.front_airbag,
        side_airbag=car_data.side_airbag,

        # Structure (from car_data)
        crumple_zone_length=car_data.crumple_zone_length_m,
        cabin_rigidity=car_data.cabin_rigidity,
        intrusion=car_data.intrusion_cm / 100  # cm → m
    )


@api_blueprint.route('/evaluate-crash', methods=['POST'])
def evaluate_crash():
    """
    POST /api/evaluate-crash

    Main endpoint for AI-enhanced crash risk analysis with auto-save to MongoDB.

    Request Body: JSON with "car_data" and "dummy_data" objects

    Returns:
        JSON response with AI-enhanced crash risk analysis and simulation ID
    """
    try:
        # Get JSON from request
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400

        # Validate with Pydantic - separate models
        try:
            car_data = CarDataModel(**data.get('car_data', {}))
            dummy_data = DummyDataModel(**data.get('dummy_data', {}))
        except ValidationError as e:
            return jsonify({
                "success": False,
                "error": "Validation error",
                "details": e.errors()
            }), 400

        # Step 1: Run baseline physics calculation
        crash_inputs = transform_request_to_crash_inputs(car_data, dummy_data)
        try:
            baseline_results = calculate_baseline_risk(crash_inputs)
        except Exception as e:
            return jsonify({
                "success": False,
                "error": "Calculation error",
                "message": str(e)
            }), 500

        # Step 2: Scrape external safety data
        car_params, dummy_details = convert_to_scraper_models(car_data, dummy_data)
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            scraped_context = loop.run_until_complete(
                scrape_safety_data(car_params, dummy_details)
            )
            loop.close()
        except Exception as e:
            scraped_context = {
                "summaryText": "External data unavailable",
                "genderBiasNotes": [],
                "dataSources": []
            }
            print(f"Scraper error: {e}")

        # Step 3: Call Gemini with baseline + scraped context
        gemini_result = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            gemini_result = loop.run_until_complete(
                analyze_with_gemini(baseline_results, scraped_context)
            )
            loop.close()

            # Format comprehensive response
            response = format_analysis_for_response(
                gemini_result,
                baseline_results,
                scraped_context
            )
            
        except ValueError as e:
            # Gemini API not configured - return baseline only
            response = {
                "success": True,
                "error": "Gemini API not configured",
                "message": str(e),
                "risk_score": baseline_results.get("risk_score_0_100", 0),
                "confidence": 0.5,
                "explanation": "Baseline calculation only (Gemini unavailable)",
                "baseline_results": baseline_results,
                "scraped_context": scraped_context
            }
            
        except Exception as e:
            # Gemini call failed - return baseline + scraper results
            response = {
                "success": True,
                "error": "Gemini analysis failed",
                "message": str(e),
                "risk_score": baseline_results.get("risk_score_0_100", 0),
                "confidence": 0.5,
                "explanation": "Baseline calculation only (Gemini error)",
                "baseline_results": baseline_results,
                "scraped_context": scraped_context
            }

        # Step 4: Save to MongoDB
        try:
            simulation_id = SimulationResult.save(
                car_data=car_data.model_dump(),
                dummy_data=dummy_data.model_dump(),
                baseline_results=baseline_results,
                gemini_analysis={
                    "risk_score": response.get("risk_score"),
                    "confidence": response.get("confidence"),
                    "explanation": response.get("explanation"),
                    "gender_bias_insights": response.get("gender_bias_insights", [])
                } if gemini_result else None,
                scraped_context=scraped_context
            )
            response["simulation_id"] = simulation_id
            response["saved"] = True
        except Exception as e:
            print(f"MongoDB save error: {e}")
            response["saved"] = False
            response["save_error"] = str(e)

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": str(e)
        }), 500


@api_blueprint.route('/history', methods=['GET'])
def get_simulation_history():
    """
    GET /api/history
    
    Retrieve all past simulation results.
    
    Query parameters:
    - limit: max number of results (default 50)
    - skip: number of results to skip (default 0)
    - crash_type: filter by crash type (frontal/side/rear)
    - gender: filter by occupant gender (male/female)
    - pregnant: filter by pregnancy status (true/false)
    
    Returns:
        JSON array of simulation results
    """
    try:
        # Get query parameters
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100
        skip = int(request.args.get('skip', 0))
        crash_type = request.args.get('crash_type')
        gender = request.args.get('gender')
        pregnant = request.args.get('pregnant')
        
        # Convert pregnant to boolean if provided
        if pregnant is not None:
            pregnant = pregnant.lower() == 'true'
        
        # Get simulations with filters
        if crash_type or gender or pregnant is not None:
            simulations = SimulationResult.get_by_filters(
                crash_type=crash_type,
                gender=gender,
                pregnant=pregnant,
                limit=limit
            )
        else:
            simulations = SimulationResult.get_all(limit=limit, skip=skip)
        
        # Get total count
        total_count = SimulationResult.count_all()
        
        return jsonify({
            "success": True,
            "simulations": simulations,
            "count": len(simulations),
            "total": total_count,
            "limit": limit,
            "skip": skip
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Failed to retrieve history",
            "message": str(e)
        }), 500


@api_blueprint.route('/history/<simulation_id>', methods=['GET'])
def get_simulation_by_id(simulation_id: str):
    """
    GET /api/history/<simulation_id>
    
    Retrieve a single simulation by ID.
    
    Returns:
        JSON object with simulation details
    """
    try:
        simulation = SimulationResult.get_by_id(simulation_id)
        
        if not simulation:
            return jsonify({
                "success": False,
                "error": "Simulation not found"
            }), 404
        
        return jsonify({
            "success": True,
            "simulation": simulation
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Failed to retrieve simulation",
            "message": str(e)
        }), 500


@api_blueprint.route('/history/<simulation_id>', methods=['DELETE'])
def delete_simulation(simulation_id: str):
    """
    DELETE /api/history/<simulation_id>
    
    Delete a simulation by ID.
    
    Returns:
        JSON confirmation message
    """
    try:
        success = SimulationResult.delete_by_id(simulation_id)
        
        if not success:
            return jsonify({
                "success": False,
                "error": "Simulation not found or already deleted"
            }), 404
        
        return jsonify({
            "success": True,
            "message": "Simulation deleted successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Failed to delete simulation",
            "message": str(e)
        }), 500


@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    GET /api/health

    Health check endpoint for monitoring.

    Returns:
        JSON with status message
    """
    return jsonify({
        "status": "healthy",
        "service": "Safety1st Crash Risk Calculator API",
        "version": "1.0.0"
    }), 200
