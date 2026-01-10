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

# Risk curve parameters for injury probabilities (placeholders - should be calibrated from NHTSA/IIHS data)
# Logistic function: P = 1 / (1 + exp(-k * (X - X50)))
RISK_CURVES = {
    "head_HIC15": {
        "X50": 700.0,   # HIC15 value at 50% risk
        "k": 0.006      # slope parameter
    },
    "neck_Nij": {
        "X50": 1.0,     # Nij value at 50% risk
        "k": 2.5        # slope parameter
    },
    "chest_A3ms": {
        "X50": 60.0,    # g's at 50% risk
        "k": 0.08       # slope parameter
    },
    "chest_deflection": {
        "X50": 0.050,   # meters at 50% risk (50mm)
        "k": 50.0       # slope parameter
    },
    "femur_load": {
        "X50": 10000.0, # Newtons at 50% risk (10 kN)
        "k": 0.0003     # slope parameter
    }
}

# Neck intercepts for Nij calculation (dummy-dependent, using 50th percentile male as default)
NECK_INTERCEPTS = {
    "F_int": 6806.0,   # N (axial force intercept)
    "M_int": 310.0     # N·m (bending moment intercept)
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
                 gender: str = "male",          # "male" or "female"
                 is_pregnant: bool = False,

                 # NEW: Seating position parameters (affect injury risk)
                 seat_distance_from_wheel: float = 0.30,  # m (distance from steering wheel/dash)
                 seat_recline_angle: float = 25.0,        # degrees from vertical (0=upright, 45=reclined)
                 seat_height_relative_to_dash: float = 0.0,  # m (negative=below, positive=above)
                 torso_length: float = None,              # m (if None, scaled from height)

                 # NEW: Occupant-specific vulnerabilities
                 neck_strength: str = "average",  # "weak", "average", "strong" (age/fitness dependent)

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
        Adjusted slightly for gender (females have ~10% lighter heads for same body mass).
        """
        base_mass = self.occupant_mass * HEAD_MASS_FRACTION

        if self.gender == "female":
            base_mass *= 0.95  # Females have slightly lighter heads relative to body mass

        return base_mass

    def _calculate_torso_mass(self) -> float:
        """
        Calculate effective torso mass for chest loading.
        Torso mass is approximately 46.7% of total body mass.
        Increased during pregnancy.
        """
        base_mass = self.occupant_mass * TORSO_MASS_FRACTION

        if self.is_pregnant:
            base_mass *= 1.15  # Pregnancy adds ~10-15% to torso mass

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
        Taller people have longer necks and greater moment arms.
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

    Process:
    1. Compute delta-V from impact parameters
    2. Generate crash pulse (acceleration vs time)
    3. Map vehicle pulse to occupant loads
    4. Compute injury criteria (HIC15, Nij, chest, femur)
    5. Convert criteria to injury probabilities
    6. Combine into overall risk score (0-100)
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
        chest_deflection = self._compute_chest_deflection(a_occ_peak)
        femur_load = self._compute_femur_load(a_occ_peak)

        # Step 6: Convert to injury probabilities
        p_head = self._logistic_risk("head_HIC15", hic15)
        p_neck = self._logistic_risk("neck_Nij", nij)
        p_chest_accel = self._logistic_risk("chest_A3ms", chest_a3ms)
        p_chest_defl = self._logistic_risk("chest_deflection", chest_deflection)
        p_chest = max(p_chest_accel, p_chest_defl)  # Take worse of two chest metrics
        p_femur = self._logistic_risk("femur_load", femur_load)

        # Step 7: Combine into overall risk
        p_baseline = self._combine_injury_probabilities(
            [p_head, p_neck, p_chest, p_femur])
        risk_score = p_baseline * 100.0

        # Package results
        self.results = {
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
            "chest_A3ms_g": round(chest_a3ms, 1),
            "chest_deflection_mm": round(chest_deflection * 1000, 1),
            "femur_load_kN": round(femur_load / 1000, 1),

            # Injury probabilities
            "P_head": round(p_head, 4),
            "P_neck": round(p_neck, 4),
            "P_chest": round(p_chest, 4),
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
            "seat_distance_from_wheel_m": self.inputs.seat_distance_from_wheel,
            "seat_recline_angle_deg": self.inputs.seat_recline_angle,
            "seat_height_relative_to_dash_m": self.inputs.seat_height_relative_to_dash,
            "torso_length_m": round(self.inputs.torso_length, 3),
            "neck_strength": self.inputs.neck_strength,

            # Assumptions and notes
            "assumptions": [
                "Rigid barrier impact (infinite mass)",
                f"Coefficient of restitution: {self.inputs.coefficient_restitution}",
                f"Pulse shape: half-sine over {pulse_duration*1000:.1f} ms",
                f"Restraint model: {self._get_restraint_type_string()}",
                f"Biomechanical parameters scaled from occupant mass ({self.inputs.occupant_mass} kg) and height ({self.inputs.occupant_height} m)",
                "Neck loads estimated from head inertia (no direct sensor)",
                f"Neck injury adjusted for '{self.inputs.neck_strength}' neck strength and {self.inputs.seat_recline_angle}° recline",
                "Chest deflection from simplified spring model",
                f"Seat distance from wheel: {self.inputs.seat_distance_from_wheel} m (optimal: 0.25-0.30 m)",
                "Femur load from effective leg mass",
                "Risk curves are placeholders - need NHTSA/IIHS calibration"
            ]
        }

        return self.results

    # ================== Step 1: Delta-V Calculation ==================

    def _compute_delta_v(self) -> float:
        """
        Compute vehicle delta-V for rigid barrier impact.

        Formula: Δv ≈ (1 + e) * v0
        where:
            e = coefficient of restitution (0 for perfectly inelastic)
            v0 = impact speed

        Returns: delta-V in m/s
        """
        v0 = self.inputs.impact_speed
        e = self.inputs.coefficient_restitution

        # For rigid barrier (m2 → ∞)
        delta_v = (1 + e) * v0

        return delta_v

    # ================== Step 2: Crash Pulse Generation ==================

    def _get_pulse_duration(self) -> float:
        """Get crash pulse duration based on impact configuration."""
        return PULSE_DURATIONS.get(self.inputs.crash_side, 0.10)

    def _compute_peak_acceleration(self, delta_v: float, T: float) -> float:
        """
        Compute peak acceleration for half-sine pulse.

        For a half-sine pulse: a(t) = a_peak * sin(πt/T)
        The integral must equal Δv:
            Δv = ∫₀ᵀ a(t) dt = a_peak * 2T/π

        Therefore: a_peak = (π/2) * (Δv/T)

        Returns: peak acceleration in m/s²
        """
        a_peak = (math.pi / 2.0) * (delta_v / T)
        return a_peak

    def _generate_crash_pulse(self, a_peak: float, T: float,
                               sample_rate: int = 10000) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate half-sine crash pulse time history.

        Args:
            a_peak: peak acceleration (m/s²)
            T: pulse duration (s)
            sample_rate: samples per second (Hz)

        Returns:
            (time_array, acceleration_mps2, acceleration_g)
        """
        n_samples = int(T * sample_rate)
        time_array = np.linspace(0, T, n_samples)

        # Half-sine pulse
        a_vehicle = a_peak * np.sin(math.pi * time_array / T)
        a_vehicle_g = a_vehicle / GRAVITY

        return time_array, a_vehicle, a_vehicle_g

    # ================== Step 3: Occupant Load Transfer ==================

    def _get_restraint_transfer_factor(self) -> float:
        """
        Determine restraint effectiveness transfer factor (alpha).
        This factor scales how much of the vehicle pulse reaches the occupant.
        """
        has_airbag = (self.inputs.front_airbag if self.inputs.crash_side == "frontal"
                      else self.inputs.side_airbag)

        if self.inputs.seatbelt_used and has_airbag:
            alpha = RESTRAINT_ALPHA["belt_and_airbag"]
        elif self.inputs.seatbelt_used:
            alpha = RESTRAINT_ALPHA["belt_only"]
        else:
            alpha = RESTRAINT_ALPHA["unbelted"]

        # Adjust for advanced features
        if self.inputs.seatbelt_pretensioner:
            alpha *= 0.95  # Pretensioner slightly reduces peak loads
        if self.inputs.seatbelt_load_limiter:
            alpha *= 0.98  # Load limiter helps at very high loads

        return alpha

    def _get_restraint_type_string(self) -> str:
        """Generate human-readable restraint configuration."""
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
        """
        Compute Head Injury Criterion with 15ms window (HIC15).

        HIC = max { (t₂ - t₁) * [ (1/(t₂-t₁)) * ∫ₜ₁ᵗ² aₐ(t) dt ]^2.5 }
        subject to: t₂ - t₁ ≤ 0.015 s

        Args:
            time_array: time points (s)
            a_g: acceleration in g's

        Returns: HIC15 (unitless)
        """
        dt = time_array[1] - time_array[0]
        max_window_samples = int(0.015 / dt)  # 15 ms window

        hic_max = 0.0

        # Slide window through time series
        for i in range(len(a_g) - 1):
            for j in range(i + 1, min(i + max_window_samples + 1, len(a_g))):
                t1 = time_array[i]
                t2 = time_array[j]
                duration = t2 - t1

                if duration > 0.015:
                    continue

                # Compute average acceleration over window
                avg_a = np.mean(a_g[i:j])

                # HIC formula
                hic_value = duration * (avg_a ** 2.5)

                if hic_value > hic_max:
                    hic_max = hic_value

        return hic_max

    def _compute_nij(self, a_occ_peak: float) -> float:
        """
        Compute Neck Injury Criterion (Nij).

        Nij = Fz/F_int + My/M_int

        Baseline approximation (without direct neck sensors):
            Fz ≈ m_head * a_occ_peak
            My ≈ Fz * lever_arm (scaled to occupant height)

        Adjusted for neck strength and seating position.

        Args:
            a_occ_peak: peak occupant acceleration (m/s²)

        Returns: Nij (unitless)
        """
        # Estimate neck axial force from head inertia
        F_z = self.inputs.head_mass * a_occ_peak  # N

        # Estimate bending moment using scaled lever arm
        M_y = F_z * self.inputs.neck_lever_arm  # N·m

        # Adjust moment for seat recline (reclined = more bending)
        recline_factor = 1.0 + (self.inputs.seat_recline_angle / 100.0)  # 25° → 1.25x
        M_y *= recline_factor

        # Normalize by intercepts
        nij_base = (F_z / NECK_INTERCEPTS["F_int"]) + (M_y / NECK_INTERCEPTS["M_int"])

        # Adjust for neck strength
        strength_multipliers = {
            "weak": 1.3,      # Elderly, children, or those with neck issues
            "average": 1.0,
            "strong": 0.85    # Athletic, well-conditioned neck muscles
        }
        nij = nij_base * strength_multipliers.get(self.inputs.neck_strength, 1.0)

        return nij

    def _compute_chest_a3ms(self, time_array: np.ndarray, a_g: np.ndarray) -> float:
        """
        Compute 3ms chest acceleration clip.

        This is the maximum average acceleration over any 3ms window.

        Args:
            time_array: time points (s)
            a_g: acceleration in g's

        Returns: A3ms in g's
        """
        dt = time_array[1] - time_array[0]
        window_samples = int(0.003 / dt)  # 3 ms window

        # For chest, we can use a beta factor close to alpha
        # (chest accelerates similarly to head for this baseline)
        # Already applied in a_occ_g, so just find max 3ms average

        max_avg = 0.0
        for i in range(len(a_g) - window_samples):
            avg_a = np.mean(a_g[i:i + window_samples])
            if avg_a > max_avg:
                max_avg = avg_a

        return max_avg

    def _compute_chest_deflection(self, a_occ_peak: float) -> float:
        """
        Compute chest deflection using simplified spring model.

        x_chest_peak ≈ γ * (m_torso * a_occ_peak) / k_belt

        Accounts for:
        - Airbag presence (distributes load)
        - Seat distance (closer to airbag = better timing)
        - Torso mass (scaled to occupant)

        Args:
            a_occ_peak: peak occupant acceleration (m/s²)

        Returns: chest deflection in meters
        """
        # Tuning factor (decreases with airbag)
        gamma = 0.8

        if self.inputs.front_airbag and self.inputs.crash_side == "frontal":
            gamma *= 0.7  # Airbag distributes load

            # Seat distance affects airbag effectiveness
            # Optimal distance: 25-30 cm. Too close (<15cm) = airbag injury risk
            # Too far (>50cm) = reduced effectiveness
            if self.inputs.seat_distance_from_wheel < 0.15:
                gamma *= 1.3  # Too close - airbag deployment can cause injury
            elif self.inputs.seat_distance_from_wheel > 0.50:
                gamma *= 1.2  # Too far - occupant moves more before contact

        # Effective belt stiffness
        k_belt = DEFAULT_BELT_STIFFNESS

        # Force on chest (uses scaled torso mass)
        F_chest = self.inputs.torso_mass * a_occ_peak

        # Deflection
        x_chest = gamma * F_chest / k_belt

        # Pregnancy increases abdominal compression risk (different injury mode)
        if self.inputs.is_pregnant:
            x_chest *= 1.1  # Flag higher risk (Gemini should elaborate)

        return x_chest

    def _compute_femur_load(self, a_occ_peak: float) -> float:
        """
        Compute femur axial load (baseline approximation).

        F_femur ≈ m_leg_eff * a_occ_peak

        Args:
            a_occ_peak: peak occupant acceleration (m/s²)

        Returns: femur load in N
        """
        F_femur = self.inputs.leg_mass * a_occ_peak
        return F_femur

    # ================== Step 5: Injury Probability Conversion ==================

    def _logistic_risk(self, criterion: str, value: float) -> float:
        """
        Convert injury criterion to probability using logistic risk curve.

        P = 1 / (1 + exp(-k * (X - X50)))

        Args:
            criterion: key into RISK_CURVES dict
            value: measured criterion value

        Returns: probability [0, 1]
        """
        params = RISK_CURVES[criterion]
        X50 = params["X50"]
        k = params["k"]

        exponent = -k * (value - X50)

        # Prevent overflow
        if exponent > 50:
            return 0.0
        elif exponent < -50:
            return 1.0

        p = 1.0 / (1.0 + math.exp(exponent))
        return p

    # ================== Step 6: Overall Risk Combination ==================

    def _combine_injury_probabilities(self, probabilities: List[float]) -> float:
        """
        Combine individual injury probabilities into overall risk.

        Assumes independence (not strictly true, but acceptable baseline):
        P_combined = 1 - ∏(1 - Pᵢ)

        Args:
            probabilities: list of individual injury probabilities

        Returns: combined probability [0, 1]
        """
        p_no_injury = 1.0
        for p in probabilities:
            p_no_injury *= (1.0 - p)

        p_baseline = 1.0 - p_no_injury
        return p_baseline


# ================== Convenience Functions ==================

def calculate_baseline_risk(inputs: CrashInputs) -> Dict[str, Any]:
    """
    Convenience function to run full baseline risk calculation.

    Args:
        inputs: CrashInputs object with all crash parameters

    Returns:
        Dictionary with all results and context for Gemini analysis
    """
    calculator = BaselineRiskCalculator(inputs)
    return calculator.calculate_all()


def format_results_for_gemini(results: Dict[str, Any]) -> str:
    """
    Format calculation results as structured text for Gemini prompt.

    Args:
        results: output from calculate_baseline_risk()

    Returns:
        Formatted string ready for Gemini API
    """
    lines = [
        "=== BASELINE CRASH RISK CALCULATION RESULTS ===",
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
        f"  Nij: {results['Nij']}",
        f"  Chest 3ms clip: {results['chest_A3ms_g']} g",
        f"  Chest deflection: {results['chest_deflection_mm']} mm",
        f"  Femur load: {results['femur_load_kN']} kN",
        "",
        "INJURY PROBABILITIES:",
        f"  Head: {results['P_head']*100:.2f}%",
        f"  Neck: {results['P_neck']*100:.2f}%",
        f"  Chest: {results['P_chest']*100:.2f}%",
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
