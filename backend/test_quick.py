"""
Quick Test Suite for Safety1st - Windows Compatible
Tests realistic crash scenarios including pregnancy
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from modeling.calculator import CrashInputs, calculate_baseline_risk


def test_realistic_speeds():
    """Test realistic crash speeds (30-60 km/h)"""
    print("\n" + "="*70)
    print(" TEST: Realistic Crash Speeds (Modern Restraints)")
    print("="*70)

    speeds = [30, 35, 40, 45, 50, 55, 60]

    for speed_kmh in speeds:
        mps = speed_kmh / 3.6
        inputs = CrashInputs(
            impact_speed=mps,
            vehicle_mass=1500.0,
            crash_side='frontal',
            coefficient_restitution=0.0,
            occupant_mass=75.0,
            occupant_height=1.75,
            gender='male',
            is_pregnant=False,
            seat_position='driver',
            pelvis_lap_belt_fit='average',
            # Modern safety features
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
        safe = risk <= 40
        status = "PASS" if safe else "FAIL"

        print(f"{speed_kmh:3d} km/h: Risk={risk:5.1f}%, " +
              f"Chest={results['thorax_irtracc_max_deflection_proxy_mm']:4.1f}mm " +
              f"[{status}]")

    print()


def test_gender_differences():
    """Test male vs female risk differences"""
    print("="*70)
    print(" TEST: Gender-Specific Risk (45 km/h Frontal)")
    print("="*70)

    scenarios = [
        {
            "name": "Average Male",
            "mass": 75.0,
            "height": 1.75,
            "gender": "male",
            "pregnant": False
        },
        {
            "name": "Average Female",
            "mass": 65.0,
            "height": 1.65,
            "gender": "female",
            "pregnant": False
        },
        {
            "name": "Pregnant Female",
            "mass": 70.0,  # Pregnancy adds ~5kg
            "height": 1.65,
            "gender": "female",
            "pregnant": True
        }
    ]

    for scenario in scenarios:
        inputs = CrashInputs(
            impact_speed=45.0 / 3.6,  # 45 km/h
            vehicle_mass=1500.0,
            crash_side='frontal',
            coefficient_restitution=0.0,
            occupant_mass=scenario["mass"],
            occupant_height=scenario["height"],
            gender=scenario["gender"],
            is_pregnant=scenario["pregnant"],
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
        safe = risk <= 40
        status = "PASS" if safe else "FAIL"

        # Check gender-specific seating defaults were applied
        seat_dist = results['seat_distance_from_wheel_m']

        print(f"{scenario['name']:20s}: Risk={risk:5.1f}%, " +
              f"Seat={seat_dist:.2f}m, " +
              f"Chest={results['thorax_irtracc_max_deflection_proxy_mm']:4.1f}mm " +
              f"[{status}]")

    print()


def test_safety_features():
    """Test impact of safety features"""
    print("="*70)
    print(" TEST: Safety Feature Impact (50 km/h Frontal)")
    print("="*70)

    configs = [
        {
            "name": "Full Modern Safety",
            "pretensioner": True,
            "load_limiter": True,
            "airbag": True
        },
        {
            "name": "Basic Belt + Airbag",
            "pretensioner": False,
            "load_limiter": False,
            "airbag": True
        },
        {
            "name": "Belt Only",
            "pretensioner": False,
            "load_limiter": False,
            "airbag": False
        }
    ]

    for config in configs:
        inputs = CrashInputs(
            impact_speed=50.0 / 3.6,
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
            seatbelt_pretensioner=config["pretensioner"],
            seatbelt_load_limiter=config["load_limiter"],
            front_airbag=config["airbag"],
            side_airbag=False,
            crumple_zone_length=0.6,
            cabin_rigidity='medium',
            intrusion=0.0
        )

        results = calculate_baseline_risk(inputs)
        risk = results['risk_score_0_100']
        safe = risk <= 40
        status = "PASS" if safe else "FAIL"

        print(f"{config['name']:20s}: Risk={risk:5.1f}%, " +
              f"Chest={results['thorax_irtracc_max_deflection_proxy_mm']:4.1f}mm " +
              f"[{status}]")

    print()


def test_production_threshold():
    """Test production safety threshold"""
    print("="*70)
    print(" TEST: Production Safety Threshold")
    print("="*70)

    from config.settings import Config
    threshold = Config.PRODUCTION_SAFETY_THRESHOLD

    print(f"Current threshold: {threshold}")
    print()

    # Test a good scenario
    inputs_good = CrashInputs(
        impact_speed=40.0 / 3.6,  # 40 km/h (low speed)
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

    results_good = calculate_baseline_risk(inputs_good)
    risk_good = results_good['risk_score_0_100']
    safe_good = results_good['risk_score_0_100'] <= threshold

    print(f"Good scenario (40 km/h): Risk={risk_good:.1f}%, Safe={safe_good}")

    # Test a marginal scenario
    inputs_marginal = CrashInputs(
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

    results_marginal = calculate_baseline_risk(inputs_marginal)
    risk_marginal = results_marginal['risk_score_0_100']
    safe_marginal = risk_marginal <= threshold

    print(f"Marginal scenario (50 km/h): Risk={risk_marginal:.1f}%, Safe={safe_marginal}")
    print()


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" Safety1st Quick Test Suite")
    print("="*70)

    try:
        test_realistic_speeds()
        test_gender_differences()
        test_safety_features()
        test_production_threshold()

        print("="*70)
        print(" ALL TESTS COMPLETED")
        print("="*70)
        print()

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
