"""
Flask API routes for Safety1st crash risk calculation.
"""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from typing import Dict, Any

from models.carDataModel import CarDataModel
from models.dummyDataModel import DummyDataModel
from modeling.calculator import (
    CrashInputs,
    calculate_baseline_risk,
    format_results_for_gemini
)

# Create Flask blueprint
api_blueprint = Blueprint('api', __name__)


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

    Enhanced endpoint that includes Gemini AI analysis.

    Request Body: JSON with "car_data" and "dummy_data" objects

    Returns:
        JSON response with baseline calculation + AI-enhanced analysis
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

        # Format for Gemini
        gemini_formatted = format_results_for_gemini(results)

        # TODO: Call Gemini API here
        # For now, return baseline + formatted text
        response = format_response(results)
        response["gemini_analysis_input"] = gemini_formatted
        response["gemini_analysis_output"] = "Gemini integration pending - see geminiAPI.py"

        return jsonify(response), 200

    except Exception as e:
        # Catch-all for unexpected errors
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": str(e)
        }), 500


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
