"""
Full End-to-End Integration Test Suite for Safety1st
Tests complete pipeline: Input → Calculator → Scraper → Gemini → Final Risk Score
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from modeling.calculator import CrashInputs, calculate_baseline_risk
from modeling.geminiAPI import analyze_with_gemini, format_analysis_for_response
from scraper.scraper import scrape_safety_data
from models.carDataModel import CarParameters
from models.dummyDataModel import DummyDetails

# Test counters
tests_passed = 0
tests_failed = 0

def test_result(name: str, passed: bool, details: str = ""):
    global tests_passed, tests_failed
    status = "PASS" if passed else "FAIL"
    symbol = "✓" if passed else "✗"
    print(f"  {symbol} {status}: {name}")
    if details:
        print(f"    {details}")
    if passed:
        tests_passed += 1
    else:
        tests_failed += 1


print("\n" + "="*80)
print("FULL END-TO-END INTEGRATION TEST SUITE")
print("="*80)


# ==============================================================================
# TEST 1: MALE DRIVER - MODERATE SPEED (50 km/h)
# ==============================================================================
print("\n" + "="*80)
print("TEST 1: MALE DRIVER - 50 km/h FRONTAL CRASH")
print("="*80)

print("\nStep 1: Create input parameters")
inputs_male = CrashInputs(
    impact_speed=50.0 / 3.6,  # 50 km/h
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
print(f"  Input: Male, 75kg, 1.75m, 50 km/h frontal")

print("\nStep 2: Calculate baseline physics risk")
baseline_male = calculate_baseline_risk(inputs_male)
baseline_risk_male = baseline_male['risk_score_0_100']
print(f"  Baseline Risk: {baseline_risk_male:.1f}%")
print(f"  HIC15: {baseline_male['HIC15']:.1f}")
print(f"  Chest Deflection: {baseline_male['thorax_irtracc_max_deflection_proxy_mm']:.1f}mm")
test_result("Baseline calculation complete", baseline_risk_male > 0)

print("\nStep 3: Scrape safety research data")
car_params = CarParameters(
    crash_side='frontal',
    vehicle_mass=1500.0,
    crumple_zone_length=0.6,
    cabin_rigidity='medium',
    seatbelt_pretensioner=True,
    seatbelt_load_limiter=True,
    front_airbags=True,
    side_airbags=False
)
dummy_params = DummyDetails(
    gender='male',
    pregnant=False,
    mass_kg=75.0,
    height_m=1.75
)

async def test_male_scraper():
    scraped_male = await scrape_safety_data(car_params, dummy_params)
    sources_count = len(scraped_male['dataSources'])
    print(f"  Scraped {sources_count} data sources")
    test_result("Scraper returned data", sources_count > 0)
    return scraped_male

scraped_male = asyncio.run(test_male_scraper())

print("\nStep 4: Analyze with Gemini AI")
async def test_male_gemini():
    gemini_result = await analyze_with_gemini(baseline_male, scraped_male)
    print(f"  Gemini Risk Score: {gemini_result.risk_score:.1f}%")
    print(f"  Confidence: {gemini_result.confidence*100:.0f}%")
    print(f"  Adjustment from baseline: {gemini_result.risk_score - baseline_risk_male:+.1f} points")

    # Validate adjustment is reasonable
    deviation = abs(gemini_result.risk_score - baseline_risk_male)
    test_result("Gemini adjustment within ±20 points", deviation <= 20,
                f"Deviation: {deviation:.1f} points")

    return gemini_result

gemini_male = asyncio.run(test_male_gemini())

print("\nStep 5: Format final API response")
final_response_male = format_analysis_for_response(gemini_male, baseline_male, scraped_male)
print(f"  Final Risk Score: {final_response_male['risk_score']:.1f}%")
print(f"  Safe for Production: {final_response_male['safe_for_production']}")
print(f"  Gender Bias Insights: {len(final_response_male['gender_bias_insights'])}")
test_result("Final response formatted", 'risk_score' in final_response_male)


# ==============================================================================
# TEST 2: FEMALE DRIVER - SAME SPEED (50 km/h)
# ==============================================================================
print("\n" + "="*80)
print("TEST 2: FEMALE DRIVER - 50 km/h FRONTAL CRASH")
print("="*80)

print("\nStep 1: Create input parameters (female)")
inputs_female = CrashInputs(
    impact_speed=50.0 / 3.6,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    occupant_mass=65.0,  # Lighter
    occupant_height=1.65,  # Shorter
    gender='female',
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
print(f"  Input: Female, 65kg, 1.65m, 50 km/h frontal")

print("\nStep 2: Calculate baseline physics risk")
baseline_female = calculate_baseline_risk(inputs_female)
baseline_risk_female = baseline_female['risk_score_0_100']
print(f"  Baseline Risk: {baseline_risk_female:.1f}%")
print(f"  Seat Distance: {baseline_female['seat_distance_from_wheel_m']:.2f}m (should be 0.25m)")
print(f"  Chest Deflection: {baseline_female['thorax_irtracc_max_deflection_proxy_mm']:.1f}mm")

# Validate gender differences
risk_diff = baseline_risk_female - baseline_risk_male
test_result("Female baseline risk > Male baseline risk", risk_diff > 0,
            f"Female: {baseline_risk_female:.1f}%, Male: {baseline_risk_male:.1f}% (Diff: +{risk_diff:.1f}%)")

print("\nStep 3: Scrape safety research data (female)")
dummy_params_female = DummyDetails(
    gender='female',
    pregnant=False,
    mass_kg=65.0,
    height_m=1.65
)

async def test_female_scraper():
    scraped_female = await scrape_safety_data(car_params, dummy_params_female)
    sources_count = len(scraped_female['dataSources'])
    print(f"  Scraped {sources_count} data sources")
    test_result("Scraper returned data", sources_count > 0)
    return scraped_female

scraped_female = asyncio.run(test_female_scraper())

print("\nStep 4: Analyze with Gemini AI")
async def test_female_gemini():
    gemini_result = await analyze_with_gemini(baseline_female, scraped_female)
    print(f"  Gemini Risk Score: {gemini_result.risk_score:.1f}%")
    print(f"  Confidence: {gemini_result.confidence*100:.0f}%")
    print(f"  Adjustment from baseline: {gemini_result.risk_score - baseline_risk_female:+.1f} points")

    # Validate adjustment
    deviation = abs(gemini_result.risk_score - baseline_risk_female)
    test_result("Gemini adjustment within ±20 points", deviation <= 20,
                f"Deviation: {deviation:.1f} points")

    return gemini_result

gemini_female = asyncio.run(test_female_gemini())

print("\nStep 5: Format final API response")
final_response_female = format_analysis_for_response(gemini_female, baseline_female, scraped_female)
print(f"  Final Risk Score: {final_response_female['risk_score']:.1f}%")
print(f"  Safe for Production: {final_response_female['safe_for_production']}")


# ==============================================================================
# TEST 3: PREGNANT FEMALE - SAME SPEED (50 km/h)
# ==============================================================================
print("\n" + "="*80)
print("TEST 3: PREGNANT FEMALE - 50 km/h FRONTAL CRASH")
print("="*80)

print("\nStep 1: Create input parameters (pregnant)")
inputs_pregnant = CrashInputs(
    impact_speed=50.0 / 3.6,
    vehicle_mass=1500.0,
    crash_side='frontal',
    coefficient_restitution=0.0,
    occupant_mass=70.0,  # +5kg pregnancy weight
    occupant_height=1.65,
    gender='female',
    is_pregnant=True,
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
print(f"  Input: Pregnant Female, 70kg, 1.65m, 50 km/h frontal")

print("\nStep 2: Calculate baseline physics risk")
baseline_pregnant = calculate_baseline_risk(inputs_pregnant)
baseline_risk_pregnant = baseline_pregnant['risk_score_0_100']
print(f"  Baseline Risk: {baseline_risk_pregnant:.1f}%")
print(f"  Chest Deflection: {baseline_pregnant['thorax_irtracc_max_deflection_proxy_mm']:.1f}mm")

# Validate pregnancy increases risk
pregnancy_diff = baseline_risk_pregnant - baseline_risk_female
test_result("Pregnancy increases baseline risk", pregnancy_diff > 0,
            f"Pregnant: {baseline_risk_pregnant:.1f}%, Non-pregnant: {baseline_risk_female:.1f}% (Diff: +{pregnancy_diff:.1f}%)")

print("\nStep 3: Scrape pregnancy-specific research")
dummy_params_pregnant = DummyDetails(
    gender='female',
    pregnant=True,
    mass_kg=70.0,
    height_m=1.65
)

async def test_pregnant_scraper():
    scraped_pregnant = await scrape_safety_data(car_params, dummy_params_pregnant)
    sources_count = len(scraped_pregnant['dataSources'])
    print(f"  Scraped {sources_count} data sources")

    # Check for pregnancy content
    summary = scraped_pregnant['summaryText'].lower()
    has_pregnancy_content = 'pregnan' in summary or 'fetal' in summary
    test_result("Pregnancy research data found", has_pregnancy_content,
                "Found pregnancy-related keywords in scraped data" if has_pregnancy_content
                else "No pregnancy keywords found (may use general female data)")

    return scraped_pregnant

scraped_pregnant = asyncio.run(test_pregnant_scraper())

print("\nStep 4: Analyze with Gemini AI")
async def test_pregnant_gemini():
    gemini_result = await analyze_with_gemini(baseline_pregnant, scraped_pregnant)
    print(f"  Gemini Risk Score: {gemini_result.risk_score:.1f}%")
    print(f"  Confidence: {gemini_result.confidence*100:.0f}%")
    print(f"  Adjustment from baseline: {gemini_result.risk_score - baseline_risk_pregnant:+.1f} points")

    # Validate adjustment
    deviation = abs(gemini_result.risk_score - baseline_risk_pregnant)
    test_result("Gemini adjustment within ±20 points", deviation <= 20,
                f"Deviation: {deviation:.1f} points")

    return gemini_result

gemini_pregnant = asyncio.run(test_pregnant_gemini())

print("\nStep 5: Format final API response")
final_response_pregnant = format_analysis_for_response(gemini_pregnant, baseline_pregnant, scraped_pregnant)
print(f"  Final Risk Score: {final_response_pregnant['risk_score']:.1f}%")
print(f"  Safe for Production: {final_response_pregnant['safe_for_production']}")

# Validate pregnancy is reflected in final score
final_pregnancy_increase = (final_response_pregnant['risk_score'] -
                            final_response_female['risk_score'])
test_result("Pregnancy reflected in final risk", final_pregnancy_increase > 0,
            f"Increase: +{final_pregnancy_increase:.1f}% from non-pregnant female")


# ==============================================================================
# TEST 4: LOW SPEED SAFE SCENARIO (35 km/h)
# ==============================================================================
print("\n" + "="*80)
print("TEST 4: SAFE SCENARIO - 35 km/h LOW SPEED")
print("="*80)

print("\nStep 1: Create low-speed input")
inputs_safe = CrashInputs(
    impact_speed=35.0 / 3.6,  # 35 km/h - should be safe
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
print(f"  Input: Male, 75kg, 35 km/h frontal (low speed)")

print("\nStep 2-5: Full pipeline")
baseline_safe = calculate_baseline_risk(inputs_safe)
baseline_risk_safe = baseline_safe['risk_score_0_100']
print(f"  Baseline Risk: {baseline_risk_safe:.1f}%")

async def test_safe_pipeline():
    scraped = await scrape_safety_data(car_params, dummy_params)
    gemini = await analyze_with_gemini(baseline_safe, scraped)
    final = format_analysis_for_response(gemini, baseline_safe, scraped)

    print(f"  Final Risk Score: {final['risk_score']:.1f}%")
    print(f"  Safe for Production: {final['safe_for_production']}")

    test_result("Low speed passes production threshold", final['safe_for_production'],
                f"Risk: {final['risk_score']:.1f}% (threshold: {final['production_threshold']})")

    return final

final_safe = asyncio.run(test_safe_pipeline())


# ==============================================================================
# TEST 5: HIGH SPEED UNSAFE SCENARIO (65 km/h)
# ==============================================================================
print("\n" + "="*80)
print("TEST 5: UNSAFE SCENARIO - 65 km/h HIGH SPEED")
print("="*80)

print("\nStep 1: Create high-speed input")
inputs_unsafe = CrashInputs(
    impact_speed=65.0 / 3.6,  # 65 km/h - should be unsafe
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
print(f"  Input: Male, 75kg, 65 km/h frontal (high speed)")

print("\nStep 2-5: Full pipeline")
baseline_unsafe = calculate_baseline_risk(inputs_unsafe)
baseline_risk_unsafe = baseline_unsafe['risk_score_0_100']
print(f"  Baseline Risk: {baseline_risk_unsafe:.1f}%")

async def test_unsafe_pipeline():
    scraped = await scrape_safety_data(car_params, dummy_params)
    gemini = await analyze_with_gemini(baseline_unsafe, scraped)
    final = format_analysis_for_response(gemini, baseline_unsafe, scraped)

    print(f"  Final Risk Score: {final['risk_score']:.1f}%")
    print(f"  Safe for Production: {final['safe_for_production']}")

    test_result("High speed fails production threshold", not final['safe_for_production'],
                f"Risk: {final['risk_score']:.1f}% (threshold: {final['production_threshold']})")

    return final

final_unsafe = asyncio.run(test_unsafe_pipeline())


# ==============================================================================
# SUMMARY
# ==============================================================================
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)

total_tests = tests_passed + tests_failed
success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0

print(f"Tests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Total Tests:  {total_tests}")
print(f"Success Rate: {success_rate:.1f}%")
print("="*80)

if tests_failed == 0:
    print("\n🎉 ALL TESTS PASSED! Full integration pipeline working correctly.")
else:
    print(f"\n⚠️ {tests_failed} test(s) failed. Review output above.")

print()
