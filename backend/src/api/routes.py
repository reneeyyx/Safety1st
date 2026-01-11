"""
Flask API routes for Safety1st crash risk calculation.
"""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from typing import Dict, Any
import asyncio

from models.carDataModel import CarDataModel, CarParameters
from models.dummyDataModel import DummyDataModel, DummyDetails
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


def format_response(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format calculator results for API response.

    Args:
        results: Raw calculator output dictionary

    Returns:
        Formatted response with structured sections
    """
    return {
        "success": True,
        "risk_score": results["risk_score_0_100"],

        "injury_criteria": {
            "HIC15": results["HIC15"],
            "Nij": results["Nij"],
            "chest_A3ms_g": results["chest_A3ms_g"],
            "chest_deflection_mm": results["chest_deflection_mm"],
            "femur_load_kN": results["femur_load_kN"]
        },

        "injury_probabilities": {
            "P_head": results["P_head"],
            "P_neck": results["P_neck"],
            "P_chest": results["P_chest"],
            "P_femur": results["P_femur"],
            "P_baseline": results["P_baseline"]
        },

        "crash_dynamics": {
            "delta_v_mps": results["delta_v_mps"],
            "pulse_duration_s": results["pulse_duration_s"],
            "pulse_type": results["pulse_type"],
            "peak_accel_g": results["peak_accel_g"],
            "restraint_type": results["restraint_type"],
            "restraint_transfer_factor": results["restraint_transfer_factor"]
        },

        "occupant_biomechanics": {
            "occupant_mass_kg": results["occupant_mass_kg"],
            "occupant_height_m": results["occupant_height_m"],
            "occupant_gender": results["occupant_gender"],
            "is_pregnant": results["is_pregnant"],
            "calculated_head_mass_kg": results["calculated_head_mass_kg"],
            "calculated_torso_mass_kg": results["calculated_torso_mass_kg"],
            "calculated_leg_mass_kg": results["calculated_leg_mass_kg"],
            "calculated_neck_lever_arm_m": results["calculated_neck_lever_arm_m"]
        },

        "seating_position": {
            "seat_distance_from_wheel_m": results["seat_distance_from_wheel_m"],
            "seat_recline_angle_deg": results["seat_recline_angle_deg"],
            "seat_height_relative_to_dash_m": results["seat_height_relative_to_dash_m"],
            "torso_length_m": results["torso_length_m"],
            "neck_strength": results["neck_strength"]
        },

        "vehicle_details": {
            "crash_configuration": results["crash_configuration"],
            "vehicle_mass_kg": results["vehicle_mass_kg"],
            "crumple_zone_m": results["crumple_zone_m"],
            "cabin_rigidity": results["cabin_rigidity"],
            "intrusion_m": results["intrusion_m"]
        },

        "assumptions": results["assumptions"],

        # Include full results for advanced users/debugging
        "full_results": results
    }


@api_blueprint.route('/crash-risk/calculate', methods=['POST'])
def calculate_crash_risk():
    """
    POST /api/crash-risk/calculate

    Main endpoint for crash risk calculation.

    Request Body: JSON with "car_data" and "dummy_data" objects

    Returns:
        JSON response with risk score, injury criteria, probabilities, and context
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

        # Transform to CrashInputs
        crash_inputs = transform_request_to_crash_inputs(car_data, dummy_data)

        # Run calculation
        try:
            results = calculate_baseline_risk(crash_inputs)
        except Exception as e:
            return jsonify({
                "success": False,
                "error": "Calculation error",
                "message": str(e)
            }), 500

        # Format and return response
        response = format_response(results)
        return jsonify(response), 200

    except Exception as e:
        # Catch-all for unexpected errors
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": str(e)
        }), 500


@api_blueprint.route('/crash-risk/analyze', methods=['POST'])
def analyze_crash_risk_with_gemini():
    """
    POST /api/crash-risk/analyze

    Enhanced endpoint that includes Gemini AI analysis with web-scraped context.

    Request Body: JSON with "car_data" and "dummy_data" objects

    Returns:
        JSON response with:
        - risk_score: 0-100 (AI-adjusted)
        - confidence: 0-1
        - explanation: detailed text explanation
        - gender_bias_insights: list of insights
        - baseline: physics calculation results
        - data_sources: list of URLs used
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
            # Run async scraper in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            scraped_context = loop.run_until_complete(
                scrape_safety_data(car_params, dummy_details)
            )
            loop.close()
        except Exception as e:
            # If scraper fails, use empty context
            scraped_context = {
                "summaryText": "External data unavailable",
                "genderBiasNotes": [],
                "dataSources": []
            }
            print(f"Scraper error: {e}")

        # Step 3: Call Gemini with baseline + scraped context
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
            return jsonify(response), 200

        except ValueError as e:
            # Gemini API not configured - return baseline only
            return jsonify({
                "success": False,
                "error": "Gemini API not configured",
                "message": str(e),
                "baseline_results": baseline_results,
                "scraped_context": scraped_context
            }), 503

        except Exception as e:
            # Gemini call failed - return baseline + scraper results
            return jsonify({
                "success": False,
                "error": "Gemini analysis failed",
                "message": str(e),
                "baseline_results": baseline_results,
                "scraped_context": scraped_context
            }), 500

    except Exception as e:
        # Catch-all for unexpected errors
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": str(e)
        }), 500


@api_blueprint.route('/evaluate-crash', methods=['POST'])
def evaluate_crash():
    """
    POST /api/evaluate-crash

    Alias for /api/crash-risk/analyze to match architecture documentation.
    This is the main endpoint as specified in the architecture.

    Request Body: JSON with "car_data" and "dummy_data" objects

    Returns:
        JSON response with AI-enhanced crash risk analysis
    """
    return analyze_crash_risk_with_gemini()


@api_blueprint.route('/test/example-crash', methods=['GET'])
def test_example_crash():
    """
    GET /api/test/example-crash

    Test endpoint that runs a predefined crash scenario.
    Useful for verifying the calculator is working without needing form input.

    Returns:
        JSON response with risk calculation for 50 km/h frontal crash
    """
    try:
        # Predefined scenario: 50 km/h frontal crash, average adult male, full safety features
        crash_inputs = CrashInputs(
            # Crash parameters
            impact_speed=13.89,  # 50 km/h in m/s
            vehicle_mass=1500.0,
            crash_side="frontal",
            coefficient_restitution=0.0,

            # Occupant - 50th percentile male
            occupant_mass=75.0,
            occupant_height=1.75,
            gender="male",
            is_pregnant=False,

            # Seating position - optimal
            seat_distance_from_wheel=0.30,
            seat_recline_angle=25.0,
            seat_height_relative_to_dash=0.0,
            neck_strength="average",

            # Safety features - full protection
            seatbelt_used=True,
            seatbelt_pretensioner=True,
            seatbelt_load_limiter=True,
            front_airbag=True,
            side_airbag=False,

            # Vehicle structure - good
            crumple_zone_length=0.6,
            cabin_rigidity="medium",
            intrusion=0.0
        )

        # Run calculation
        results = calculate_baseline_risk(crash_inputs)

        # Format response
        response = format_response(results)
        response["test_scenario"] = "50 km/h frontal crash, average adult male, full safety features"

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Test endpoint error",
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
