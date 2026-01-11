"""
COMPREHENSIVE TEST SUITE FOR SAFETY1ST
Tests all calculator formulas, API endpoints, scraper, and edge cases
Run with: python test_comprehensive.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import math
from modeling.calculator import CrashInputs, calculate_baseline_risk


# Test results tracking
tests_passed = 0
tests_failed = 0


def test_result(name, condition, expected="True"):
    """Track and print test results"""
    global tests_passed, tests_failed
    if condition:
        print(f"  PASS: {name}")
        tests_passed += 1
    else:
        print(f"  FAIL: {name} (expected: {expected})")
        tests_failed += 1
    return condition


print("="*80)
print("COMPREHENSIVE SAFETY1ST TEST SUITE")
print("="*80)


# ==============================================================================
# TEST 1: PHYSICS FORMULAS VALIDATION
# ==============================================================================
print("\n" + "="*80)
print("TEST 1: PHYSICS FORMULAS")
print("="*80)

print("\n1.1: Delta-V Calculation")
# Delta-V = sqrt((2 * KE) / m_vehicle) where KE from impact
inputs = CrashInputs(
    impact_speed=10.0,  # 10 m/s
    vehicle_mass=1000.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    gender='male'
)
results = calculate_baseline_risk(inputs)
delta_v = results['delta_v_mps']
# For rigid barrier: delta_v ~ impact_speed
test_result("Delta-V ~ impact speed for rigid barrier", abs(delta_v - 10.0) < 0.5, "~10 m/s")

print("\n1.2: Pulse Duration Formula (T = 2d/dv, NO SQRT!)")
# With crumple zone 0.5m and delta-v 10 m/s: T = 2*0.5/10 = 0.1s = 100ms
pulse_duration = results['pulse_duration_s']
expected_T = 2 * 0.5 / 10.0  # 0.1s
test_result("Pulse duration T=2d/dv (no sqrt)", abs(pulse_duration - expected_T) < 0.01, f"~{expected_T}s")

print("\n1.3: Peak Acceleration (a_peak = pi/2 * dv/T for half-sine)")
peak_accel_g = results['peak_accel_g']
expected_peak = (math.pi / 2) * (delta_v / pulse_duration) / 9.81  # in g's
test_result("Peak acceleration formula", abs(peak_accel_g - expected_peak) < 1.0, f"~{expected_peak:.1f}g")

print("\n1.4: Femur Risk Curve Direction (higher force = higher risk)")
# Test at low force
inputs_low_femur = CrashInputs(
    impact_speed=5.0,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    gender='male'
)
results_low = calculate_baseline_risk(inputs_low_femur)

# Test at high force
inputs_high_femur = CrashInputs(
    impact_speed=20.0,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    gender='male'
)
results_high = calculate_baseline_risk(inputs_high_femur)

femur_low = results_low['P_femur_AIS2plus_proxy']
femur_high = results_high['P_femur_AIS2plus_proxy']
test_result("Femur risk increases with speed", femur_high > femur_low, f"{femur_high:.3f} > {femur_low:.3f}")


# ==============================================================================
# TEST 2: RESTRAINT EFFECTIVENESS
# ==============================================================================
print("\n" + "="*80)
print("TEST 2: RESTRAINT EFFECTIVENESS")
print("="*80)

print("\n2.1: Pretensioner Effect")
# With pretensioner
inputs_with = CrashInputs(
    impact_speed=13.89,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    gender='male',
    seatbelt_pretensioner=True,
    seatbelt_load_limiter=False,
    front_airbag=True
)
results_with = calculate_baseline_risk(inputs_with)

# Without pretensioner
inputs_without = CrashInputs(
    impact_speed=13.89,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    gender='male',
    seatbelt_pretensioner=False,
    seatbelt_load_limiter=False,
    front_airbag=True
)
results_without = calculate_baseline_risk(inputs_without)

chest_with = results_with['thorax_irtracc_max_deflection_proxy_mm']
chest_without = results_without['thorax_irtracc_max_deflection_proxy_mm']
reduction = (chest_without - chest_with) / chest_without * 100

test_result("Pretensioner reduces chest deflection", chest_with < chest_without, f"{chest_with:.1f} < {chest_without:.1f}")
test_result("Pretensioner gives ~25% reduction", abs(reduction - 25) < 10, f"~25% (got {reduction:.1f}%)")

print("\n2.2: Load Limiter Effect")
# With load limiter
inputs_ll = CrashInputs(
    impact_speed=13.89,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    gender='male',
    seatbelt_pretensioner=False,
    seatbelt_load_limiter=True,
    front_airbag=True
)
results_ll = calculate_baseline_risk(inputs_ll)

chest_ll = results_ll['thorax_irtracc_max_deflection_proxy_mm']
reduction_ll = (chest_without - chest_ll) / chest_without * 100

test_result("Load limiter reduces chest deflection", chest_ll < chest_without, f"{chest_ll:.1f} < {chest_without:.1f}")
test_result("Load limiter gives ~15% reduction", abs(reduction_ll - 15) < 10, f"~15% (got {reduction_ll:.1f}%)")


# ==============================================================================
# TEST 3: GENDER-SPECIFIC FEATURES
# ==============================================================================
print("\n" + "="*80)
print("TEST 3: GENDER-SPECIFIC FEATURES")
print("="*80)

print("\n3.1: Gender-Specific Seating Defaults")
# Male - should use male defaults
inputs_male = CrashInputs(
    impact_speed=13.89,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    occupant_mass=75.0,
    occupant_height=1.75,
    gender='male',
    # Not specifying seat distance - should use male default
)
results_male = calculate_baseline_risk(inputs_male)
male_seat_dist = results_male['seat_distance_from_wheel_m']

# Female - should use female defaults
inputs_female = CrashInputs(
    impact_speed=13.89,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    occupant_mass=65.0,
    occupant_height=1.65,
    gender='female',
    # Not specifying seat distance - should use female default
)
results_female = calculate_baseline_risk(inputs_female)
female_seat_dist = results_female['seat_distance_from_wheel_m']

test_result("Male sits farther than female", male_seat_dist > female_seat_dist, f"{male_seat_dist:.2f} > {female_seat_dist:.2f}")
test_result("Male seat distance ~0.35m", abs(male_seat_dist - 0.35) < 0.01, "0.35m")
test_result("Female seat distance ~0.25m", abs(female_seat_dist - 0.25) < 0.01, "0.25m")

print("\n3.2: Pregnancy Impact")
# Non-pregnant
inputs_not_pregnant = CrashInputs(
    impact_speed=13.89,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    occupant_mass=65.0,
    occupant_height=1.65,
    gender='female',
    is_pregnant=False
)
results_not_pregnant = calculate_baseline_risk(inputs_not_pregnant)

# Pregnant
inputs_pregnant = CrashInputs(
    impact_speed=13.89,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    occupant_mass=70.0,  # +5kg for pregnancy
    occupant_height=1.65,
    gender='female',
    is_pregnant=True
)
results_pregnant = calculate_baseline_risk(inputs_pregnant)

risk_not_pregnant = results_not_pregnant['risk_score_0_100']
risk_pregnant = results_pregnant['risk_score_0_100']

test_result("Pregnancy increases risk", risk_pregnant > risk_not_pregnant, f"{risk_pregnant:.1f} > {risk_not_pregnant:.1f}")
test_result("Pregnancy increases torso mass",
            inputs_pregnant.torso_mass > inputs_not_pregnant.torso_mass,
            f"{inputs_pregnant.torso_mass:.1f} > {inputs_not_pregnant.torso_mass:.1f}")


# ==============================================================================
# TEST 4: REALISTIC CRASH SCENARIOS
# ==============================================================================
print("\n" + "="*80)
print("TEST 4: REALISTIC CRASH SCENARIOS")
print("="*80)

print("\n4.1: Low-Speed Crashes (30-45 km/h) Should Pass")
for speed_kmh in [30, 35, 40, 45]:
    inputs = CrashInputs(
        impact_speed=speed_kmh / 3.6,
        vehicle_mass=1500.0,
        crash_side='frontal',
        coefficient_restitution=0.0,
        occupant_mass=75.0,
        occupant_height=1.75,
        gender='male',
        is_pregnant=False,
        seat_position='driver',
        pelvis_lap_belt_fit='average',
        seatbelt_used=True,
        seatbelt_pretensioner=True,
        seatbelt_load_limiter=True,
        front_airbag=True,
        side_airbag=False,
        crumple_zone_length=0.6,
        cabin_rigidity='medium',
        intrusion=0.0
    )
    results = calculate_baseline_risk(inputs)
    risk = results['risk_score_0_100']
    test_result(f"{speed_kmh} km/h with modern safety passes threshold", risk <= 40, f"risk={risk:.1f}")

print("\n4.2: High-Speed Crashes (50+ km/h) Should Fail")
for speed_kmh in [50, 55, 60]:
    inputs = CrashInputs(
        impact_speed=speed_kmh / 3.6,
        vehicle_mass=1500.0,
        crash_side='frontal',
        coefficient_restitution=0.0,
        occupant_mass=75.0,
        occupant_height=1.75,
        gender='male',
        is_pregnant=False,
        seat_position='driver',
        pelvis_lap_belt_fit='average',
        seatbelt_used=True,
        seatbelt_pretensioner=True,
        seatbelt_load_limiter=True,
        front_airbag=True,
        side_airbag=False,
        crumple_zone_length=0.6,
        cabin_rigidity='medium',
        intrusion=0.0
    )
    results = calculate_baseline_risk(inputs)
    risk = results['risk_score_0_100']
    test_result(f"{speed_kmh} km/h with modern safety fails threshold", risk > 40, f"risk={risk:.1f}")


# ==============================================================================
# TEST 5: PRODUCTION SAFETY THRESHOLD
# ==============================================================================
print("\n" + "="*80)
print("TEST 5: PRODUCTION SAFETY THRESHOLD")
print("="*80)

from config.settings import Config

print(f"\n5.1: Current Threshold = {Config.PRODUCTION_SAFETY_THRESHOLD}")

# Test a PASS scenario
inputs_pass = CrashInputs(
    impact_speed=40.0 / 3.6,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    gender='male',
    seatbelt_pretensioner=True,
    seatbelt_load_limiter=True,
    front_airbag=True
)
results_pass = calculate_baseline_risk(inputs_pass)
test_result("40 km/h scenario PASSES threshold",
            results_pass['risk_score_0_100'] <= Config.PRODUCTION_SAFETY_THRESHOLD,
            f"risk={results_pass['risk_score_0_100']:.1f}")

# Test a FAIL scenario
inputs_fail = CrashInputs(
    impact_speed=50.0 / 3.6,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    gender='male',
    seatbelt_pretensioner=True,
    seatbelt_load_limiter=True,
    front_airbag=True
)
results_fail = calculate_baseline_risk(inputs_fail)
test_result("50 km/h scenario FAILS threshold",
            results_fail['risk_score_0_100'] > Config.PRODUCTION_SAFETY_THRESHOLD,
            f"risk={results_fail['risk_score_0_100']:.1f}")


# ==============================================================================
# TEST 6: EDGE CASES
# ==============================================================================
print("\n" + "="*80)
print("TEST 6: EDGE CASES")
print("="*80)

print("\n6.1: No Safety Features")
inputs_unsafe = CrashInputs(
    impact_speed=13.89,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    gender='male',
    seatbelt_used=False,
    seatbelt_pretensioner=False,
    seatbelt_load_limiter=False,
    front_airbag=False
)
results_unsafe = calculate_baseline_risk(inputs_unsafe)
test_result("No safety features gives very high risk",
            results_unsafe['risk_score_0_100'] > 90,
            f"risk={results_unsafe['risk_score_0_100']:.1f}")

print("\n6.2: Very Low Speed")
inputs_very_low = CrashInputs(
    impact_speed=2.0,  # 7.2 km/h
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    gender='male'
)
results_very_low = calculate_baseline_risk(inputs_very_low)
test_result("Very low speed gives low risk",
            results_very_low['risk_score_0_100'] < 5,
            f"risk={results_very_low['risk_score_0_100']:.1f}")

print("\n6.3: Extreme Intrusion")
inputs_intrusion = CrashInputs(
    impact_speed=13.89,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    gender='male',
    intrusion=0.30,  # 30cm intrusion
    seatbelt_pretensioner=True,
    seatbelt_load_limiter=True,
    front_airbag=True
)
results_intrusion = calculate_baseline_risk(inputs_intrusion)

inputs_no_intrusion = CrashInputs(
    impact_speed=13.89,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    gender='male',
    intrusion=0.0,
    seatbelt_pretensioner=True,
    seatbelt_load_limiter=True,
    front_airbag=True
)
results_no_intrusion = calculate_baseline_risk(inputs_no_intrusion)

test_result("Intrusion increases risk",
            results_intrusion['risk_score_0_100'] > results_no_intrusion['risk_score_0_100'],
            f"{results_intrusion['risk_score_0_100']:.1f} > {results_no_intrusion['risk_score_0_100']:.1f}")


# ==============================================================================
# TEST 7: API INTEGRATION
# ==============================================================================
print("\n" + "="*80)
print("TEST 7: FLASK API INTEGRATION")
print("="*80)

try:
    from main import create_app

    app = create_app()
    client = app.test_client()

    print("\n7.1: Health Check")
    response = client.get('/api/health')
    test_result("Health check returns 200", response.status_code == 200)

    print("\n7.2: Test Endpoint")
    response = client.get('/api/test/example-crash')
    test_result("Test endpoint returns 200", response.status_code == 200)
    if response.status_code == 200:
        data = response.get_json()
        test_result("Response has risk_score", 'risk_score' in data)
        test_result("Response has safe_for_production", 'safe_for_production' in data)
        test_result("Response has production_threshold", 'production_threshold' in data)

    print("\n7.3: Calculate Endpoint")
    payload = {
        "car_data": {
            "impact_speed_kmh": 40.0,
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

    response = client.post('/api/crash-risk/calculate',
                          json=payload,
                          content_type='application/json')
    test_result("Calculate endpoint returns 200", response.status_code == 200)
    if response.status_code == 200:
        data = response.get_json()
        test_result("Calculate has all required fields",
                   all(k in data for k in ['risk_score', 'safe_for_production', 'injury_criteria']))

except Exception as e:
    print(f"  FAIL: API tests failed: {e}")
    tests_failed += 3


# ==============================================================================
# FINAL SUMMARY
# ==============================================================================
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print(f"Tests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Total Tests:  {tests_passed + tests_failed}")
print(f"Success Rate: {tests_passed/(tests_passed+tests_failed)*100:.1f}%")
print("="*80)

if tests_failed == 0:
    print("\n ALL TESTS PASSED!")
    sys.exit(0)
else:
    print(f"\n {tests_failed} TEST(S) FAILED!")
    sys.exit(1)
