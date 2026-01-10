"""
Baseline crash risk calculation module
Implements physics-based injury criteria (HIC15, Nij, chest, femur)
and converts to injury probabilities and risk scores.
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Any


# Physical constants
GRAVITY = 9.80665  # m/s²

# Reference biomechanical parameters (50th percentile male, 75 kg)
# These will be scaled based on actual occupant mass and height
REFERENCE_BODY_MASS = 75.0  # kg
REFERENCE_HEIGHT = 1.75  # m (50th percentile male)
REFERENCE_HEAD_MASS = 4.75  # kg (6.3% of body mass)
REFERENCE_TORSO_MASS = 35.0  # kg (46.7% of body mass)
REFERENCE_LEG_MASS = 10.0  # kg (13.3% of body mass)
REFERENCE_NECK_LEVER_ARM = 0.125  # m (scales with height)
REFERENCE_TORSO_LENGTH = 0.60  # m (scales with height)

# Body segment mass fractions (anthropometric data)
HEAD_MASS_FRACTION = REFERENCE_HEAD_MASS / REFERENCE_BODY_MASS  # ~6.3%
TORSO_MASS_FRACTION = REFERENCE_TORSO_MASS / REFERENCE_BODY_MASS  # ~46.7%
LEG_MASS_FRACTION = REFERENCE_LEG_MASS / REFERENCE_BODY_MASS  # ~13.3%

# Pulse duration defaults by impact type
PULSE_DURATIONS = {
    "frontal": 0.10,  # seconds
    "side": 0.07,     # seconds
    "rear": 0.09      # seconds
}

# Restraint transfer factors (how much vehicle pulse transfers to occupant)
RESTRAINT_ALPHA = {
    "belt_and_airbag": 0.55,
    "belt_only": 0.75,
    "unbelted": 1.05
}

# === CHANGE 1: Add a calibration/version tag so your backend & Gemini know what you used
CALIBRATION_SET = "thor_05f_ais3plus_thorax_irtracc_xy_v1"

# Risk curve parameters for injury probabilities
# Supports two forms:
#   (A) "X50"+"k"  : P = 1/(1+exp(-k*(X-X50)))
#   (B) "beta0"+"beta1": P = 1/(1+exp(-(beta0+beta1*X)))
RISK_CURVES = {
    # NOTE: head/neck/femur remain placeholders until you swap in published/specific curves.
    "head_HIC15": {
        "X50": 700.0,   # placeholder
        "k": 0.006      # placeholder
    },
    "neck_Nij": {
        "X50": 1.0,     # placeholder
        "k": 2.5        # placeholder
    },

    # === CHANGE 2: Chest risk now uses THOR-05F AIS3+ thorax IRF (logistic regression)
    # We treat X as IR-TRACC max deflection in mm (proxy-derived in this code).
    # P(AIS3+) = 1/(1 + exp(-(beta0 + beta1*X_mm)))
    "thorax_irtracc_max_deflection_mm_AIS3plus": {
        "beta0": -4.9522,   # THOR-05F matched-pair, X-Y resultant
        "beta1": 0.1657,    # THOR-05F matched-pair, X-Y resultant
        "units": "mm",
        "notes": "THOR-05F AIS3+ (>=3 rib fractures) IRF using max IR-TRACC deflection (X-Y resultant)."
    },

    # Keep these only for reporting / debugging; we will not use chest_A3ms for risk by default anymore.
    "chest_A3ms": {
        "X50": 60.0,    # placeholder
        "k": 0.08       # placeholder
    },

    # We keep femur as placeholder
    "femur_load": {
        "X50": 10000.0, # placeholder
        "k": 0.0003     # placeholder
    }
}

# Neck intercepts for Nij calculation (dummy-dependent, using 50th percentile male as default)
NECK_INTERCEPTS = {
    "F_int": 6806.0,   # N (axial force intercept) - placeholder for true Nij mode handling
    "M_int": 310.0     # N·m (bending moment intercept) - placeholder
}

# Belt stiffness approximation
DEFAULT_BELT_STIFFNESS = 50000.0  # N/m


class CrashInputs:
    """Container for crash simulation inputs"""
    def __init__(self,
                 # Vehicle/crash parameters
                 impact_speed: float,           # m/s
                 vehicle_mass: float,           # kg
                 crash_side: str,               # "frontal", "side", or "rear"
                 coefficient_restitution: float = 0.0,  # dimensionless, 0-0.3

                 # Occupant parameters
                 occupant_mass: float = 75.0,   # kg
                 occupant_height: float = 1.75, # m (IMPORTANT: used for scaling)
                 gender: str = "female",        # === CHANGE 3: default to female since you target THOR-05F
                 is_pregnant: bool = False,

                 # NEW: Seating position parameters (affect injury risk)
                 seat_distance_from_wheel: float = 0.30,  # m (distance from steering wheel/dash)
                 seat_recline_angle: float = 25.0,        # degrees from vertical (0=upright, 45=reclined)
                 seat_height_relative_to_dash: float = 0.0,  # m (negative=below, positive=above)
                 torso_length: float = None,              # m (if None, scaled from height)

                 # NEW: Occupant-specific vulnerabilities
                 neck_strength: str = "average",  # "weak", "average", "strong" (age/fitness dependent)
                 seat_position: str = "driver",    # "driver" or "passenger"
                 pelvis_lap_belt_fit: str = "average",  # "poor", "average", "good" (lap belt positioning)

                 # Restraint systems
                 seatbelt_used: bool = True,
                 seatbelt_pretensioner: bool = False,
                 seatbelt_load_limiter: bool = False,
                 front_airbag: bool = True,
                 side_airbag: bool = False,

                 # Structural parameters
                 crumple_zone_length: float = 0.5,  # m
                 cabin_rigidity: str = "medium",    # "low", "medium", "high"
                 intrusion: float = 0.0,            # m (side impacts)

                 # Optional biomechanical overrides (for advanced users)
                 head_mass: float = None,
                 torso_mass: float = None,
                 leg_mass: float = None,
                 neck_lever_arm: float = None):

        self.impact_speed = impact_speed
        self.vehicle_mass = vehicle_mass
        self.crash_side = crash_side.lower()
        self.coefficient_restitution = coefficient_restitution

        self.occupant_mass = occupant_mass
        self.occupant_height = occupant_height
        self.gender = gender.lower()
        self.is_pregnant = is_pregnant

        # Seating position
        self.seat_distance_from_wheel = seat_distance_from_wheel
        self.seat_recline_angle = seat_recline_angle
        self.seat_height_relative_to_dash = seat_height_relative_to_dash
        self.torso_length = torso_length if torso_length is not None else self._estimate_torso_length()

        # Vulnerability factors
        self.neck_strength = neck_strength.lower()
        self.seat_position = seat_position.lower()
        self.pelvis_lap_belt_fit = pelvis_lap_belt_fit.lower()

        self.seatbelt_used = seatbelt_used
        self.seatbelt_pretensioner = seatbelt_pretensioner
        self.seatbelt_load_limiter = seatbelt_load_limiter
        self.front_airbag = front_airbag
        self.side_airbag = side_airbag

        self.crumple_zone_length = crumple_zone_length
        self.cabin_rigidity = cabin_rigidity
        self.intrusion = intrusion

        # Calculate biomechanical parameters scaled to occupant size
        self.head_mass = head_mass if head_mass is not None else self._calculate_head_mass()
        self.torso_mass = torso_mass if torso_mass is not None else self._calculate_torso_mass()
        self.leg_mass = leg_mass if leg_mass is not None else self._calculate_leg_mass()
        self.neck_lever_arm = neck_lever_arm if neck_lever_arm is not None else self._calculate_neck_lever_arm()

    def _calculate_head_mass(self) -> float:
        """
        Calculate head mass proportional to body mass.
        Head mass is approximately 6.3% of total body mass.
        Adjusted slightly for gender.
        """
        base_mass = self.occupant_mass * HEAD_MASS_FRACTION

        if self.gender == "female":
            base_mass *= 0.95

        return base_mass

    def _calculate_torso_mass(self) -> float:
        """
        Calculate effective torso mass for chest loading.
        Torso mass is approximately 46.7% of total body mass.
        Increased during pregnancy.
        """
        base_mass = self.occupant_mass * TORSO_MASS_FRACTION

        if self.is_pregnant:
            base_mass *= 1.15

        return base_mass

    def _calculate_leg_mass(self) -> float:
        """
        Calculate effective leg mass for femur loading.
        Each leg is ~13.3% of body mass (one leg used for loading).
        """
        return self.occupant_mass * LEG_MASS_FRACTION

    def _calculate_neck_lever_arm(self) -> float:
        """
        Calculate neck moment arm scaled by height.
        """
        height_scaling = self.occupant_height / REFERENCE_HEIGHT
        return REFERENCE_NECK_LEVER_ARM * height_scaling

    def _estimate_torso_length(self) -> float:
        """
        Estimate torso length from overall height.
        Torso is approximately 34% of total height.
        """
        return self.occupant_height * 0.34


class BaselineRiskCalculator:
    """
    Calculates baseline crash risk scores using physics-based injury criteria.
    """

    def __init__(self, inputs: CrashInputs):
        self.inputs = inputs
        self.results = {}

    def calculate_all(self) -> Dict[str, Any]:
        """
        Execute full baseline risk calculation pipeline.
        Returns comprehensive results dictionary for Gemini analysis.
        """
        # Step 1: Compute delta-V
        delta_v = self._compute_delta_v()

        # Step 2: Determine pulse characteristics
        pulse_duration = self._get_pulse_duration()
        a_peak = self._compute_peak_acceleration(delta_v, pulse_duration)

        # Step 3: Generate acceleration time history
        time_array, a_vehicle, a_vehicle_g = self._generate_crash_pulse(
            a_peak, pulse_duration)

        # Step 4: Map to occupant loads
        alpha = self._get_restraint_transfer_factor()
        a_occ = alpha * a_vehicle
        a_occ_g = a_occ / GRAVITY
        a_occ_peak = np.max(a_occ)

        # Step 5: Compute injury criteria
        hic15 = self._compute_hic15(time_array, a_occ_g)
        nij = self._compute_nij(a_occ_peak)
        chest_a3ms = self._compute_chest_a3ms(time_array, a_occ_g)

        # Chest deflection proxy (meters) -> convert to mm for THOR-05F IRF
        chest_deflection_m = self._compute_chest_deflection(a_occ_peak)
        chest_deflection_mm = chest_deflection_m * 1000.0  # === CHANGE 4: explicit mm value for IRF

        femur_load = self._compute_femur_load(a_occ_peak)

        # Step 6: Convert to injury probabilities
        p_head = self._logistic_risk("head_HIC15", hic15)
        p_neck = self._logistic_risk("neck_Nij", nij)

        # === CHANGE 5: Chest probability uses THOR-05F thorax IRF on deflection_mm
        p_thorax = self._logistic_risk("thorax_irtracc_max_deflection_mm_AIS3plus", chest_deflection_mm)

        # Optional: keep chest accel probability as diagnostic only (NOT combined by default)
        p_chest_accel_diag = self._logistic_risk("chest_A3ms", chest_a3ms)

        p_femur = self._logistic_risk("femur_load", femur_load)

        # Step 7: Combine into overall risk
        # === CHANGE 6: Use p_thorax as the chest/thorax channel in the combined probability
        p_baseline = self._combine_injury_probabilities(
            [p_head, p_neck, p_thorax, p_femur]
        )
        risk_score = p_baseline * 100.0

        # Package results
        self.results = {
            "calibration_set": CALIBRATION_SET,  # === CHANGE 7

            # Crash dynamics
            "delta_v_mps": round(delta_v, 2),
            "pulse_duration_s": round(pulse_duration, 4),
            "pulse_type": "half-sine",
            "peak_accel_g": round(a_peak / GRAVITY, 2),

            # Restraint effectiveness
            "restraint_type": self._get_restraint_type_string(),
            "restraint_transfer_factor": round(alpha, 3),

            # Injury criteria
            "HIC15": round(hic15, 1),
            "Nij": round(nij, 3),

            # Keep A3ms (diagnostic)
            "chest_A3ms_g": round(chest_a3ms, 1),

            # === CHANGE 8: store both m + mm; mm is what the THOR-05F IRF uses
            "thorax_deflection_proxy_m": round(chest_deflection_m, 5),
            "thorax_irtracc_max_deflection_proxy_mm": round(chest_deflection_mm, 1),

            "femur_load_kN": round(femur_load / 1000, 1),

            # Injury probabilities
            "P_head": round(p_head, 4),
            "P_neck": round(p_neck, 4),

            # === CHANGE 9: Thorax probability (AIS3+) is now the “chest channel”
            "P_thorax_AIS3plus": round(p_thorax, 4),

            # Diagnostic only
            "P_chest_A3ms_diag": round(p_chest_accel_diag, 4),

            "P_femur": round(p_femur, 4),

            # Overall risk
            "P_baseline": round(p_baseline, 4),
            "risk_score_0_100": round(risk_score, 1),

            # Context for Gemini
            "crash_configuration": self.inputs.crash_side,
            "occupant_gender": self.inputs.gender,
            "occupant_mass_kg": self.inputs.occupant_mass,
            "occupant_height_m": self.inputs.occupant_height,
            "is_pregnant": self.inputs.is_pregnant,
            "vehicle_mass_kg": self.inputs.vehicle_mass,
            "crumple_zone_m": self.inputs.crumple_zone_length,
            "cabin_rigidity": self.inputs.cabin_rigidity,
            "intrusion_m": self.inputs.intrusion,

            # Biomechanical parameters (scaled to occupant)
            "calculated_head_mass_kg": round(self.inputs.head_mass, 2),
            "calculated_torso_mass_kg": round(self.inputs.torso_mass, 2),
            "calculated_leg_mass_kg": round(self.inputs.leg_mass, 2),
            "calculated_neck_lever_arm_m": round(self.inputs.neck_lever_arm, 3),

            # Seating position (affects injury risk)
            "seat_position": self.inputs.seat_position,
            "seat_distance_from_wheel_m": self.inputs.seat_distance_from_wheel,
            "seat_recline_angle_deg": self.inputs.seat_recline_angle,
            "seat_height_relative_to_dash_m": self.inputs.seat_height_relative_to_dash,
            "torso_length_m": round(self.inputs.torso_length, 3),
            "neck_strength": self.inputs.neck_strength,
            "pelvis_lap_belt_fit": self.inputs.pelvis_lap_belt_fit,

            # Assumptions and notes
            "assumptions": [
                "Rigid barrier impact (infinite mass)",
                f"Coefficient of restitution: {self.inputs.coefficient_restitution}",
                f"Pulse shape: half-sine over {pulse_duration*1000:.1f} ms",
                f"Restraint model: {self._get_restraint_type_string()}",
                f"Biomechanical parameters scaled from occupant mass ({self.inputs.occupant_mass} kg) and height ({self.inputs.occupant_height} m)",
                "Neck loads estimated from head inertia (no direct sensor) (Nij is a proxy here; not full sign/mode-based Nij)",
                f"Neck injury adjusted for '{self.inputs.neck_strength}' neck strength and {self.inputs.seat_recline_angle}° recline",
                "Chest deflection from simplified spring model",
                f"Seat position: {self.inputs.seat_position} (passenger may have different posture/bracing)",
                f"Seat distance from wheel: {self.inputs.seat_distance_from_wheel} m (optimal: 0.25-0.30 m)",
                f"Pelvis/lap belt fit: {self.inputs.pelvis_lap_belt_fit} (affects load distribution and femur loading)",
                "Femur load from effective leg mass, adjusted for pelvis fit and seat position",
                "Thorax AIS3+ probability uses THOR-05F IR-TRACC max deflection IRF (X-Y resultant) on a proxy deflection signal (spring model).",
                "Chest 3ms acceleration is computed but treated as diagnostic only in this calibration set.",
                "Head/neck/femur risk curves are still placeholders in this file; replace with published AIS3+ curves and/or THOR-05F equivalents when available."
            ]
        }

        return self.results

    # ================== Step 1: Delta-V Calculation ==================

    def _compute_delta_v(self) -> float:
        """
        Compute vehicle delta-V for rigid barrier impact.

        Formula: Δv ≈ (1 + e) * v0
        """
        v0 = self.inputs.impact_speed
        e = self.inputs.coefficient_restitution
        return (1 + e) * v0

    # ================== Step 2: Crash Pulse Generation ==================

    def _get_pulse_duration(self) -> float:
        return PULSE_DURATIONS.get(self.inputs.crash_side, 0.10)

    def _compute_peak_acceleration(self, delta_v: float, T: float) -> float:
        """
        Half-sine pulse: a_peak = (π/2) * (Δv/T)
        """
        return (math.pi / 2.0) * (delta_v / T)

    def _generate_crash_pulse(self, a_peak: float, T: float,
                              sample_rate: int = 10000) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        n_samples = int(T * sample_rate)
        time_array = np.linspace(0, T, n_samples)
        a_vehicle = a_peak * np.sin(math.pi * time_array / T)
        a_vehicle_g = a_vehicle / GRAVITY
        return time_array, a_vehicle, a_vehicle_g

    # ================== Step 3: Occupant Load Transfer ==================

    def _get_restraint_transfer_factor(self) -> float:
        has_airbag = (self.inputs.front_airbag if self.inputs.crash_side == "frontal"
                      else self.inputs.side_airbag)

        if self.inputs.seatbelt_used and has_airbag:
            alpha = RESTRAINT_ALPHA["belt_and_airbag"]
        elif self.inputs.seatbelt_used:
            alpha = RESTRAINT_ALPHA["belt_only"]
        else:
            alpha = RESTRAINT_ALPHA["unbelted"]

        if self.inputs.seatbelt_pretensioner:
            alpha *= 0.95
        if self.inputs.seatbelt_load_limiter:
            alpha *= 0.98

        return alpha

    def _get_restraint_type_string(self) -> str:
        parts = []
        if self.inputs.seatbelt_used:
            parts.append("seatbelt")
            if self.inputs.seatbelt_pretensioner:
                parts.append("pretensioner")
            if self.inputs.seatbelt_load_limiter:
                parts.append("load_limiter")
        else:
            parts.append("unbelted")

        if self.inputs.front_airbag and self.inputs.crash_side == "frontal":
            parts.append("front_airbag")
        if self.inputs.side_airbag and self.inputs.crash_side == "side":
            parts.append("side_airbag")

        return " + ".join(parts)

    # ================== Step 4: Injury Criteria Calculation ==================

    def _compute_hic15(self, time_array: np.ndarray, a_g: np.ndarray) -> float:
        dt = time_array[1] - time_array[0]
        max_window_samples = int(0.015 / dt)

        hic_max = 0.0
        for i in range(len(a_g) - 1):
            for j in range(i + 1, min(i + max_window_samples + 1, len(a_g))):
                t1 = time_array[i]
                t2 = time_array[j]
                duration = t2 - t1
                if duration <= 0.0 or duration > 0.015:
                    continue
                avg_a = np.mean(a_g[i:j])
                hic_value = duration * (avg_a ** 2.5)
                if hic_value > hic_max:
                    hic_max = hic_value
        return hic_max

    def _compute_nij(self, a_occ_peak: float) -> float:
        F_z = self.inputs.head_mass * a_occ_peak
        M_y = F_z * self.inputs.neck_lever_arm

        recline_factor = 1.0 + (self.inputs.seat_recline_angle / 100.0)
        M_y *= recline_factor

        nij_base = (F_z / NECK_INTERCEPTS["F_int"]) + (M_y / NECK_INTERCEPTS["M_int"])

        strength_multipliers = {
            "weak": 1.3,
            "average": 1.0,
            "strong": 0.85
        }
        return nij_base * strength_multipliers.get(self.inputs.neck_strength, 1.0)

    def _compute_chest_a3ms(self, time_array: np.ndarray, a_g: np.ndarray) -> float:
        dt = time_array[1] - time_array[0]
        window_samples = max(1, int(0.003 / dt))  # === CHANGE 11: guard against window_samples=0

        max_avg = 0.0
        for i in range(len(a_g) - window_samples):
            avg_a = np.mean(a_g[i:i + window_samples])
            if avg_a > max_avg:
                max_avg = avg_a
        return max_avg

    def _compute_chest_deflection(self, a_occ_peak: float) -> float:
        gamma = 0.8

        if self.inputs.front_airbag and self.inputs.crash_side == "frontal":
            gamma *= 0.7

            if self.inputs.seat_distance_from_wheel < 0.15:
                gamma *= 1.3
            elif self.inputs.seat_distance_from_wheel > 0.50:
                gamma *= 1.2

        k_belt = DEFAULT_BELT_STIFFNESS
        F_chest = self.inputs.torso_mass * a_occ_peak
        x_chest = gamma * F_chest / k_belt

        if self.inputs.is_pregnant:
            x_chest *= 1.1

        return x_chest

    def _compute_femur_load(self, a_occ_peak: float) -> float:
        """
        Compute femur axial load (baseline approximation).

        F_femur ≈ m_leg_eff * a_occ_peak * pelvis_factor

        Pelvis/lap belt fit affects load distribution:
        - Poor fit: lap belt rides up onto abdomen, less femur loading protection
        - Good fit: optimal load distribution through pelvis

        Args:
            a_occ_peak: peak occupant acceleration (m/s²)

        Returns: femur load in N
        """
        F_femur_base = self.inputs.leg_mass * a_occ_peak

        # Adjust for pelvis/lap belt fit
        pelvis_fit_factors = {
            "poor": 1.25,    # Poor fit increases femur load (less pelvic support)
            "average": 1.0,
            "good": 0.85     # Good fit reduces femur load (optimal pelvic support)
        }
        pelvis_factor = pelvis_fit_factors.get(self.inputs.pelvis_lap_belt_fit, 1.0)

        # Seat position affects loading (passenger may be more relaxed, different posture)
        position_factor = 1.05 if self.inputs.seat_position == "passenger" else 1.0

        F_femur = F_femur_base * pelvis_factor * position_factor
        return F_femur

    # ================== Step 5: Injury Probability Conversion ==================

    def _logistic_risk(self, criterion: str, value: float) -> float:
        """
        Supports:
          A) X50/k form:      P = 1/(1+exp(-k*(X-X50)))
          B) beta0/beta1 form P = 1/(1+exp(-(beta0+beta1*X)))
        """
        params = RISK_CURVES[criterion]

        # === CHANGE 12: support published beta0/beta1 curves (THOR-05F thorax IRF)
        if "beta0" in params and "beta1" in params:
            beta0 = float(params["beta0"])
            beta1 = float(params["beta1"])
            z = beta0 + beta1 * float(value)
            # clamp for numerical stability
            if z > 50:
                return 1.0
            if z < -50:
                return 0.0
            return 1.0 / (1.0 + math.exp(-z))

        # Fallback: original X50/k style
        X50 = float(params["X50"])
        k = float(params["k"])
        exponent = -k * (float(value) - X50)

        if exponent > 50:
            return 0.0
        elif exponent < -50:
            return 1.0

        return 1.0 / (1.0 + math.exp(exponent))

    # ================== Step 6: Overall Risk Combination ==================

    def _combine_injury_probabilities(self, probabilities: List[float]) -> float:
        p_no_injury = 1.0
        for p in probabilities:
            p_no_injury *= (1.0 - p)
        return 1.0 - p_no_injury


# ================== Convenience Functions ==================

def calculate_baseline_risk(inputs: CrashInputs) -> Dict[str, Any]:
    calculator = BaselineRiskCalculator(inputs)
    return calculator.calculate_all()


def format_results_for_gemini(results: Dict[str, Any]) -> str:
    lines = [
        "=== BASELINE CRASH RISK CALCULATION RESULTS ===",
        "",
        f"CALIBRATION SET: {results.get('calibration_set','unknown')}",  # === CHANGE 13
        "",
        "CRASH DYNAMICS:",
        f"  Configuration: {results['crash_configuration']}",
        f"  Delta-V: {results['delta_v_mps']} m/s",
        f"  Pulse: {results['pulse_type']} over {results['pulse_duration_s']*1000:.1f} ms",
        f"  Peak deceleration: {results['peak_accel_g']} g",
        "",
        "RESTRAINT SYSTEM:",
        f"  Type: {results['restraint_type']}",
        f"  Transfer factor: {results['restraint_transfer_factor']}",
        "",
        "INJURY CRITERIA:",
        f"  HIC15: {results['HIC15']}",
        f"  Nij (proxy): {results['Nij']}",
        f"  Chest 3ms clip (diagnostic): {results['chest_A3ms_g']} g",
        f"  Thorax deflection proxy (IR-TRACC max, mm): {results['thorax_irtracc_max_deflection_proxy_mm']} mm",  # === CHANGE 14
        f"  Femur load: {results['femur_load_kN']} kN",
        "",
        "INJURY PROBABILITIES:",
        f"  Head: {results['P_head']*100:.2f}%",
        f"  Neck: {results['P_neck']*100:.2f}%",
        f"  Thorax AIS3+: {results['P_thorax_AIS3plus']*100:.2f}%",  # === CHANGE 15
        f"  Femur: {results['P_femur']*100:.2f}%",
        "",
        "OVERALL RISK:",
        f"  Combined probability: {results['P_baseline']*100:.2f}%",
        f"  RISK SCORE: {results['risk_score_0_100']}/100",
        "",
        "OCCUPANT DETAILS:",
        f"  Gender: {results['occupant_gender']}",
        f"  Mass: {results['occupant_mass_kg']} kg",
        f"  Pregnant: {'Yes' if results['is_pregnant'] else 'No'}",
        "",
        "VEHICLE DETAILS:",
        f"  Mass: {results['vehicle_mass_kg']} kg",
        f"  Crumple zone: {results['crumple_zone_m']} m",
        f"  Cabin rigidity: {results['cabin_rigidity']}",
        f"  Intrusion: {results['intrusion_m']} m",
        "",
        "ASSUMPTIONS:",
    ]

    for assumption in results['assumptions']:
        lines.append(f"  - {assumption}")

    return "\n".join(lines)
