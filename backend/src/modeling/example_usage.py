"""
Example usage of the baseline risk calculator
"""

from calculator import CrashInputs, calculate_baseline_risk, format_results_for_gemini


def example_frontal_crash():
    """Example: Frontal crash into rigid barrier at 50 km/h - Average adult male"""

    # Create inputs
    inputs = CrashInputs(
        # Crash parameters
        impact_speed=13.89,  # m/s (50 km/h)
        vehicle_mass=1500.0,  # kg
        crash_side="frontal",
        coefficient_restitution=0.0,  # Perfectly inelastic

        # Occupant - 50th percentile male
        occupant_mass=75.0,  # kg
        occupant_height=1.75,  # m
        gender="male",
        is_pregnant=False,

        # Seating position - good position
        seat_distance_from_wheel=0.30,  # m - optimal
        seat_recline_angle=25.0,  # degrees - normal
        seat_height_relative_to_dash=0.0,
        neck_strength="average",

        # Safety features
        seatbelt_used=True,
        seatbelt_pretensioner=True,
        seatbelt_load_limiter=True,
        front_airbag=True,
        side_airbag=False,

        # Vehicle structure
        crumple_zone_length=0.6,  # m
        cabin_rigidity="medium",
        intrusion=0.0
    )

    # Calculate risk
    results = calculate_baseline_risk(inputs)

    # Print formatted results
    print(format_results_for_gemini(results))
    print("\n" + "="*60)
    print("Risk Score:", results['risk_score_0_100'], "/100")
    print("="*60)

    return results


def example_side_crash_vulnerable():
    """Example: Side impact with pregnant female occupant - Small stature, poor position"""

    inputs = CrashInputs(
        # Crash parameters
        impact_speed=15.0,  # m/s (54 km/h) - higher speed side impact
        vehicle_mass=1400.0,  # kg - lighter vehicle
        crash_side="side",
        coefficient_restitution=0.0,

        # Occupant - pregnant female, 5th percentile
        occupant_mass=55.0,  # kg - smaller female
        occupant_height=1.60,  # m - shorter stature
        gender="female",
        is_pregnant=True,

        # Seating position - suboptimal
        seat_distance_from_wheel=0.25,  # m - slightly closer
        seat_recline_angle=35.0,  # degrees - more reclined
        seat_height_relative_to_dash=-0.05,  # m - lower seat
        neck_strength="weak",  # Pregnancy + smaller stature

        # Safety features - no side airbag in this scenario
        seatbelt_used=True,
        seatbelt_pretensioner=False,
        seatbelt_load_limiter=False,
        front_airbag=False,  # Not relevant for side impact
        side_airbag=False,   # Vehicle lacks side airbags

        # Vehicle structure - worse protection
        crumple_zone_length=0.15,  # m - minimal side crumple zone
        cabin_rigidity="low",  # Weaker structure
        intrusion=0.10  # 10 cm intrusion into cabin
    )

    results = calculate_baseline_risk(inputs)

    print("\n\n")
    print(format_results_for_gemini(results))
    print("\n" + "="*60)
    print("Risk Score:", results['risk_score_0_100'], "/100")
    print("="*60)

    return results


def example_unbelted():
    """Example: Unbelted large male in frontal crash - Even at lower speed, very dangerous"""

    inputs = CrashInputs(
        impact_speed=11.11,  # m/s (40 km/h) - lower speed but still dangerous
        vehicle_mass=1600.0,  # kg
        crash_side="frontal",
        coefficient_restitution=0.0,

        # Large male
        occupant_mass=95.0,  # kg - 95th percentile
        occupant_height=1.85,  # m - tall
        gender="male",
        is_pregnant=False,

        # Poor seating position (too close, no restraints)
        seat_distance_from_wheel=0.15,  # m - dangerously close
        seat_recline_angle=20.0,
        seat_height_relative_to_dash=0.05,
        neck_strength="average",

        # NO restraints - WORST CASE
        seatbelt_used=False,
        seatbelt_pretensioner=False,
        seatbelt_load_limiter=False,
        front_airbag=False,
        side_airbag=False,

        crumple_zone_length=0.5,
        cabin_rigidity="medium",
        intrusion=0.0
    )

    results = calculate_baseline_risk(inputs)

    print("\n\n")
    print(format_results_for_gemini(results))
    print("\n" + "="*60)
    print("Risk Score:", results['risk_score_0_100'], "/100")
    print("="*60)

    return results


if __name__ == "__main__":
    print("EXAMPLE 1: Modern vehicle, frontal crash, all safety features")
    print("="*60)
    result1 = example_frontal_crash()

    print("\n\n")
    print("EXAMPLE 2: Side impact, pregnant female, no side airbag, intrusion")
    print("="*60)
    result2 = example_side_crash_vulnerable()

    print("\n\n")
    print("EXAMPLE 3: Unbelted occupant, frontal crash")
    print("="*60)
    result3 = example_unbelted()

    # Compare
    print("\n\n")
    print("="*60)
    print("COMPARISON:")
    print("="*60)
    print(f"Example 1 (safe): {result1['risk_score_0_100']}/100")
    print(f"Example 2 (vulnerable): {result2['risk_score_0_100']}/100")
    print(f"Example 3 (unbelted): {result3['risk_score_0_100']}/100")
