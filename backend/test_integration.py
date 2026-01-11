"""
Comprehensive Integration Test Suite for Safety1st
Tests the complete system: Calculator + Flask API + Scraper + Gemini (optional)

Usage:
    # Run all tests
    python test_integration.py

    # Run specific test categories
    python test_integration.py --calculator  # Only calculator tests
    python test_integration.py --api        # Only API tests
    python test_integration.py --scraper    # Only scraper tests
    python test_integration.py --full       # All tests including Gemini (requires API key)
"""

import sys
import os
import asyncio
import json
import argparse
from typing import Dict, Any

# Add src to path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

# Color output for terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(title: str):
    """Print a formatted test section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_pass(message: str):
    """Print a pass message"""
    print(f"{Colors.GREEN}✓ PASS{Colors.RESET}: {message}")

def print_fail(message: str):
    """Print a fail message"""
    print(f"{Colors.RED}✗ FAIL{Colors.RESET}: {message}")

def print_warning(message: str):
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠ WARNING{Colors.RESET}: {message}")

def print_info(message: str):
    """Print an info message"""
    print(f"{Colors.BLUE}ℹ INFO{Colors.RESET}: {message}")


# ============================================================================
# TEST 1: CALCULATOR TESTS
# ============================================================================

def test_calculator():
    """Test the baseline risk calculator"""
    print_test_header("TEST 1: BASELINE CALCULATOR")

    try:
        from modeling.calculator import CrashInputs, calculate_baseline_risk

        # Test Case 1: Standard frontal crash
        print_info("Test 1.1: Standard frontal crash (50 km/h, male, full safety)")
        inputs = CrashInputs(
            impact_speed=13.89,  # 50 km/h in m/s
            vehicle_mass=1500.0,
            crash_side="frontal",
            coefficient_restitution=0.0,
            occupant_mass=75.0,
            occupant_height=1.75,
            gender="male",
            is_pregnant=False,
            seat_distance_from_wheel=0.30,
            seat_recline_angle=25.0,
            seat_height_relative_to_dash=0.0,
            neck_strength="average",
            seatbelt_used=True,
            seatbelt_pretensioner=True,
            seatbelt_load_limiter=True,
            front_airbag=True,
            side_airbag=False,
            crumple_zone_length=0.6,
            cabin_rigidity="medium",
            intrusion=0.0
        )

        results = calculate_baseline_risk(inputs)

        # Validate results structure
        assert 'risk_score_0_100' in results, "Missing risk_score_0_100"
        assert 'HIC15' in results, "Missing HIC15"
        assert 'Nij' in results, "Missing Nij"
        assert 'P_baseline' in results, "Missing P_baseline"

        risk_score = results['risk_score_0_100']
        print_pass(f"Calculator executed successfully. Risk score: {risk_score:.1f}/100")

        # Validate risk score is reasonable
        assert 0 <= risk_score <= 100, f"Risk score {risk_score} out of bounds"
        print_pass(f"Risk score within valid range: {risk_score:.1f}/100")

        # Test Case 2: Female occupant (should show higher risk)
        print_info("Test 1.2: Female occupant (same conditions)")
        inputs.gender = "female"
        inputs.occupant_mass = 65.0
        inputs.occupant_height = 1.65

        results_female = calculate_baseline_risk(inputs)
        risk_score_female = results_female['risk_score_0_100']
        print_pass(f"Female occupant risk: {risk_score_female:.1f}/100")

        # Female should generally show higher risk
        if risk_score_female > risk_score:
            print_pass(f"Gender bias detected: Female risk ({risk_score_female:.1f}) > Male risk ({risk_score:.1f})")
        else:
            print_warning(f"Expected female risk to be higher, but got {risk_score_female:.1f} vs {risk_score:.1f}")

        # Test Case 3: No safety features (should show much higher risk)
        print_info("Test 1.3: No safety features (no seatbelt, no airbags)")
        inputs.seatbelt_used = False
        inputs.front_airbag = False
        inputs.seatbelt_pretensioner = False
        inputs.seatbelt_load_limiter = False

        results_unsafe = calculate_baseline_risk(inputs)
        risk_score_unsafe = results_unsafe['risk_score_0_100']
        print_pass(f"No safety features risk: {risk_score_unsafe:.1f}/100")

        if risk_score_unsafe > risk_score_female * 1.5:
            print_pass(f"Safety features impact validated: Unsafe ({risk_score_unsafe:.1f}) >> Safe ({risk_score_female:.1f})")
        else:
            print_warning(f"Expected much higher risk without safety features")

        # Test Case 4: Production safety flag
        print_info("Test 1.4: Production safety threshold")
        from config.settings import Config
        threshold = Config.PRODUCTION_SAFETY_THRESHOLD
        print_info(f"Production threshold: {threshold}")

        if risk_score <= threshold:
            print_pass(f"Standard scenario PASSES production threshold ({risk_score:.1f} <= {threshold})")
        else:
            print_fail(f"Standard scenario FAILS production threshold ({risk_score:.1f} > {threshold})")

        if risk_score_unsafe > threshold:
            print_pass(f"Unsafe scenario correctly FAILS production threshold ({risk_score_unsafe:.1f} > {threshold})")
        else:
            print_warning(f"Unsafe scenario should fail production threshold")

        return True

    except Exception as e:
        print_fail(f"Calculator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TEST 2: API TESTS (Flask)
# ============================================================================

def test_api():
    """Test Flask API endpoints"""
    print_test_header("TEST 2: FLASK API")

    try:
        from main import create_app
        import json

        app = create_app()
        client = app.test_client()

        # Test Case 1: Health check
        print_info("Test 2.1: Health check endpoint")
        response = client.get('/api/health')
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        data = response.get_json()
        assert data['status'] == 'healthy', "Health check returned unhealthy"
        print_pass("Health check endpoint working")

        # Test Case 2: Test endpoint (predefined scenario)
        print_info("Test 2.2: Test endpoint (GET /api/test/example-crash)")
        response = client.get('/api/test/example-crash')
        assert response.status_code == 200, f"Test endpoint failed: {response.status_code}"
        data = response.get_json()
        assert data['success'] == True, "Test endpoint returned success=False"
        assert 'risk_score' in data, "Missing risk_score in response"
        assert 'safe_for_production' in data, "Missing safe_for_production flag"
        assert 'production_threshold' in data, "Missing production_threshold"
        print_pass(f"Test endpoint working. Risk: {data['risk_score']:.1f}, Safe: {data['safe_for_production']}")

        # Test Case 3: Calculate endpoint (POST with full payload)
        print_info("Test 2.3: Calculate endpoint (POST /api/crash-risk/calculate)")
        payload = {
            "car_data": {
                "impact_speed_kmh": 50.0,
                "crash_side": "frontal",
                "vehicle_mass_kg": 1500.0,
                "crumple_zone_length_m": 0.6,
                "cabin_rigidity": "medium",
                "intrusion_cm": 0.0,
                "seatbelt_used": True,
                "seatbelt_pretensioner": True,
                "seatbelt_load_limiter": True,
                "front_airbag": True,
                "side_airbag": False
            },
            "dummy_data": {
                "occupant_mass_kg": 75.0,
                "occupant_height_m": 1.75,
                "gender": "male",
                "is_pregnant": False,
                "seat_distance_from_wheel_cm": 30.0,
                "seat_recline_angle_deg": 25.0,
                "seat_height_relative_to_dash_cm": 0.0,
                "neck_strength": "average",
                "seat_position": "driver",
                "pelvis_lap_belt_fit": "average"
            }
        }

        response = client.post(
            '/api/crash-risk/calculate',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert response.status_code == 200, f"Calculate endpoint failed: {response.status_code}"
        data = response.get_json()
        assert data['success'] == True, "Calculate endpoint returned success=False"
        assert 'safe_for_production' in data, "Missing production safety flag"
        print_pass(f"Calculate endpoint working. Risk: {data['risk_score']:.1f}, Safe: {data['safe_for_production']}")

        # Test Case 4: Validation (invalid input)
        print_info("Test 2.4: Validation (invalid speed)")
        invalid_payload = payload.copy()
        invalid_payload['car_data']['impact_speed_kmh'] = 999  # Too high

        response = client.post(
            '/api/crash-risk/calculate',
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print_pass("Validation correctly rejected invalid input")

        # Test Case 5: Unit conversion verification
        print_info("Test 2.5: Unit conversion (km/h to m/s)")
        # Test that 100 km/h input gets converted to ~27.78 m/s
        payload_100kmh = payload.copy()
        payload_100kmh['car_data']['impact_speed_kmh'] = 100.0

        response = client.post(
            '/api/crash-risk/calculate',
            data=json.dumps(payload_100kmh),
            content_type='application/json'
        )
        data = response.get_json()
        delta_v = data['crash_dynamics']['delta_v_mps']
        # Should be close to 27.78 m/s (100 km/h)
        expected = 100 / 3.6
        if abs(delta_v - expected) < 0.5:
            print_pass(f"Unit conversion correct: 100 km/h → {delta_v:.2f} m/s (expected {expected:.2f})")
        else:
            print_fail(f"Unit conversion wrong: expected {expected:.2f} m/s, got {delta_v:.2f}")

        return True

    except Exception as e:
        print_fail(f"API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TEST 3: SCRAPER TESTS
# ============================================================================

async def test_scraper_async():
    """Test web scraper (async)"""
    print_test_header("TEST 3: WEB SCRAPER")

    try:
        from models.carDataModel import CarParameters
        from models.dummyDataModel import DummyDetails
        from scraper import scrape_safety_data

        # Test Case 1: Standard scrape
        print_info("Test 3.1: Scrape safety data for frontal crash")
        car_params = CarParameters(
            crash_side="frontal",
            vehicle_mass=1500,
            crumple_zone_length=0.6,
            cabin_rigidity="medium",
            seatbelt_pretensioner=True,
            seatbelt_load_limiter=True,
            front_airbags=True,
            side_airbags=False
        )

        dummy_details = DummyDetails(
            gender="female",
            seat_position="driver",
            pregnant=False,
            pelvis_lap_belt_fit="average"
        )

        result = await scrape_safety_data(car_params, dummy_details)

        assert 'summaryText' in result, "Missing summaryText"
        assert 'genderBiasNotes' in result, "Missing genderBiasNotes"
        assert 'dataSources' in result, "Missing dataSources"
        print_pass("Scraper returned valid structure")

        # Check if data sources were successfully scraped
        if result['dataSources']:
            print_pass(f"Scraped {len(result['dataSources'])} data sources")
            for source in result['dataSources']:
                print_info(f"  - {source}")
        else:
            print_warning("No data sources scraped (all URLs may have failed)")

        # Check gender bias notes
        if result['genderBiasNotes']:
            print_pass(f"Found {len(result['genderBiasNotes'])} gender bias notes")
            for note in result['genderBiasNotes']:
                print_info(f"  - {note[:80]}...")
        else:
            print_warning("No gender-specific notes found")

        # Test Case 2: Pregnant occupant
        print_info("Test 3.2: Scrape for pregnant occupant")
        dummy_details.pregnant = True
        result_pregnant = await scrape_safety_data(car_params, dummy_details)

        # Should mention pregnant somewhere
        if 'pregnant' in result_pregnant['summaryText'].lower() or \
           any('pregnant' in note.lower() for note in result_pregnant['genderBiasNotes']):
            print_pass("Scraper correctly incorporated pregnancy context")
        else:
            print_warning("Expected pregnancy to be mentioned in scraped context")

        return True

    except Exception as e:
        print_fail(f"Scraper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scraper():
    """Wrapper to run async scraper tests"""
    return asyncio.run(test_scraper_async())


# ============================================================================
# TEST 4: GEMINI INTEGRATION (Optional - requires API key)
# ============================================================================

async def test_gemini_async():
    """Test Gemini AI integration (requires API key)"""
    print_test_header("TEST 4: GEMINI AI INTEGRATION")

    try:
        from config.settings import Config
        from modeling.geminiAPI import analyze_with_gemini
        from modeling.calculator import CrashInputs, calculate_baseline_risk
        from models.carDataModel import CarParameters
        from models.dummyDataModel import DummyDetails
        from scraper import scrape_safety_data

        # Check if API key is configured
        if not Config.GEMINI_API_KEY:
            print_warning("Gemini API key not configured. Skipping Gemini tests.")
            print_info("Set GEMINI_API_KEY environment variable to run Gemini tests")
            return True  # Skip, but don't fail

        print_info("Test 4.1: Full pipeline (Calculator → Scraper → Gemini)")

        # Step 1: Run calculator
        inputs = CrashInputs(
            impact_speed=13.89,
            vehicle_mass=1500.0,
            crash_side="frontal",
            coefficient_restitution=0.0,
            occupant_mass=65.0,
            occupant_height=1.65,
            gender="female",
            is_pregnant=False,
            seat_distance_from_wheel=0.30,
            seat_recline_angle=25.0,
            seat_height_relative_to_dash=0.0,
            neck_strength="average",
            seat_position="driver",
            pelvis_lap_belt_fit="average",
            seatbelt_used=True,
            seatbelt_pretensioner=True,
            seatbelt_load_limiter=True,
            front_airbag=True,
            side_airbag=False,
            crumple_zone_length=0.6,
            cabin_rigidity="medium",
            intrusion=0.0
        )

        baseline_results = calculate_baseline_risk(inputs)
        print_pass(f"Baseline calculated: {baseline_results['risk_score_0_100']:.1f}/100")

        # Step 2: Scrape data
        car_params = CarParameters(
            crash_side="frontal",
            vehicle_mass=1500,
            crumple_zone_length=0.6,
            cabin_rigidity="medium",
            seatbelt_pretensioner=True,
            seatbelt_load_limiter=True,
            front_airbags=True,
            side_airbags=False
        )
        dummy_details = DummyDetails(
            gender="female",
            seat_position="driver",
            pregnant=False,
            pelvis_lap_belt_fit="average"
        )

        scraped_context = await scrape_safety_data(car_params, dummy_details)
        print_pass(f"Scraped {len(scraped_context['dataSources'])} data sources")

        # Step 3: Analyze with Gemini
        print_info("Calling Gemini API (this may take 5-10 seconds)...")
        gemini_result = await analyze_with_gemini(baseline_results, scraped_context)

        assert gemini_result.risk_score >= 0, "Invalid risk score"
        assert gemini_result.risk_score <= 100, "Invalid risk score"
        assert gemini_result.confidence >= 0, "Invalid confidence"
        assert gemini_result.confidence <= 1, "Invalid confidence"
        assert len(gemini_result.explanation) > 0, "Empty explanation"
        print_pass(f"Gemini analysis complete: {gemini_result.risk_score:.1f}/100 (confidence: {gemini_result.confidence:.2%})")

        # Compare baseline vs Gemini
        baseline_score = baseline_results['risk_score_0_100']
        gemini_score = gemini_result.risk_score
        diff = abs(gemini_score - baseline_score)
        print_info(f"Baseline: {baseline_score:.1f}, Gemini: {gemini_score:.1f}, Difference: {diff:.1f}")

        if diff < 50:
            print_pass("Gemini adjustment is reasonable (< 50 point difference)")
        else:
            print_warning(f"Large difference between baseline and Gemini ({diff:.1f} points)")

        # Check gender bias insights
        if gemini_result.gender_bias_insights:
            print_pass(f"Gemini provided {len(gemini_result.gender_bias_insights)} gender bias insights")
            for insight in gemini_result.gender_bias_insights:
                print_info(f"  - {insight[:80]}...")
        else:
            print_warning("Gemini did not provide gender bias insights")

        return True

    except Exception as e:
        print_fail(f"Gemini integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gemini():
    """Wrapper to run async Gemini tests"""
    return asyncio.run(test_gemini_async())


# ============================================================================
# TEST 5: END-TO-END API TEST (with Gemini endpoint)
# ============================================================================

def test_api_gemini():
    """Test Flask API with Gemini endpoint"""
    print_test_header("TEST 5: API WITH GEMINI")

    try:
        from main import create_app
        from config.settings import Config
        import json

        if not Config.GEMINI_API_KEY:
            print_warning("Gemini API key not configured. Skipping API+Gemini tests.")
            return True  # Skip, but don't fail

        app = create_app()
        client = app.test_client()

        print_info("Test 5.1: Analyze endpoint (POST /api/crash-risk/analyze)")
        payload = {
            "car_data": {
                "impact_speed_kmh": 50.0,
                "crash_side": "frontal",
                "vehicle_mass_kg": 1500.0,
                "crumple_zone_length_m": 0.6,
                "cabin_rigidity": "medium",
                "intrusion_cm": 0.0,
                "seatbelt_used": True,
                "seatbelt_pretensioner": True,
                "seatbelt_load_limiter": True,
                "front_airbag": True,
                "side_airbag": False
            },
            "dummy_data": {
                "occupant_mass_kg": 65.0,
                "occupant_height_m": 1.65,
                "gender": "female",
                "is_pregnant": False,
                "seat_distance_from_wheel_cm": 30.0,
                "seat_recline_angle_deg": 25.0,
                "seat_height_relative_to_dash_cm": 0.0,
                "neck_strength": "average",
                "seat_position": "driver",
                "pelvis_lap_belt_fit": "average"
            }
        }

        print_info("Calling API (may take 10-15 seconds for scraping + Gemini)...")
        response = client.post(
            '/api/crash-risk/analyze',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Analyze endpoint failed: {response.status_code}"
        data = response.get_json()

        assert data['success'] == True, "Analyze endpoint returned success=False"
        assert 'risk_score' in data, "Missing risk_score"
        assert 'confidence' in data, "Missing confidence"
        assert 'explanation' in data, "Missing explanation"
        assert 'gender_bias_insights' in data, "Missing gender_bias_insights"
        assert 'safe_for_production' in data, "Missing safe_for_production flag"
        assert 'baseline' in data, "Missing baseline results"
        assert 'data_sources' in data, "Missing data sources"

        print_pass(f"Analyze endpoint working")
        print_info(f"  Risk: {data['risk_score']:.1f}/100")
        print_info(f"  Confidence: {data['confidence']:.2%}")
        print_info(f"  Safe for production: {data['safe_for_production']}")
        print_info(f"  Baseline risk: {data['baseline']['risk_score']:.1f}")
        print_info(f"  Data sources: {len(data['data_sources'])}")

        return True

    except Exception as e:
        print_fail(f"API+Gemini test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='Safety1st Integration Test Suite')
    parser.add_argument('--calculator', action='store_true', help='Run only calculator tests')
    parser.add_argument('--api', action='store_true', help='Run only API tests')
    parser.add_argument('--scraper', action='store_true', help='Run only scraper tests')
    parser.add_argument('--full', action='store_true', help='Run all tests including Gemini')
    args = parser.parse_args()

    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Safety1st Integration Test Suite{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")

    results = {}

    # Determine which tests to run
    run_all = not (args.calculator or args.api or args.scraper or args.full)

    if args.calculator or run_all:
        results['calculator'] = test_calculator()

    if args.api or run_all:
        results['api'] = test_api()

    if args.scraper or run_all:
        results['scraper'] = test_scraper()

    if args.full:
        results['gemini'] = test_gemini()
        results['api_gemini'] = test_api_gemini()

    # Print summary
    print_test_header("TEST SUMMARY")

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests

    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASSED{Colors.RESET}" if result else f"{Colors.RED}FAILED{Colors.RESET}"
        print(f"{test_name.upper()}: {status}")

    print(f"\n{Colors.BOLD}Total: {total_tests} | Passed: {passed_tests} | Failed: {failed_tests}{Colors.RESET}\n")

    if failed_tests > 0:
        print_fail(f"{failed_tests} test(s) failed")
        sys.exit(1)
    else:
        print_pass("All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
