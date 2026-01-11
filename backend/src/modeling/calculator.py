"""
Baseline crash risk calculation module
Implements physics-based injury criteria (HIC15, Nij, thorax, femur)
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

# Calibration/version tag
CALIBRATION_SET = "thor_05f_ais3plus_thorax_irtracc_xy_v1_ncap_head_neck_kth_femur_v1_corrcombo_nij_dyn_v1"

# === NEW: Correlation factor for combining injury probabilities
# corr_factor = 1.0 -> independence (original behavior)
# corr_factor < 1.0 -> positive correlation (injuries cluster), so union risk grows more slowly
DEFAULT_INJURY_CORRELATION_FACTOR = 0.75

# Risk curve parameters for injury probabilities
# Supported forms:
#   (A) "X50"+"k"                : P = 1/(1+exp(-k*(X-X50)))                     (legacy)
#   (B) "beta0"+"beta1"          : P = 1/(1+exp(-(beta0+beta1*X)))               (logistic)
#   (C) "form"="probit_lognormal": P = Phi((ln(X)-mu)/sigma)                     (probit on log)
RISK_CURVES = {
    # Head AIS3+ (probit on ln(HIC15))
    "head_HIC15_AIS3plus_probit": {
        "form": "probit_lognormal",
        "mu": 7.45231,
        "sigma": 0.73998,
        "units": "HIC15",
        "notes": "Head AIS3+ risk from probit on ln(HIC15)."
    },

    # Neck AIS3+ (logistic on Nij)
    "neck_Nij_AIS3plus": {
        "beta0": -3.227,
        "beta1": 1.969,
        "units": "Nij",
        "notes": "Neck AIS3+ risk from logistic model on Nij."
    },

    # THOR-05F Thorax AIS3+ IRF (logistic on IR-TRACC max deflection, mm)
    "thorax_irtracc_max_deflection_mm_AIS3plus": {
        "beta0": -4.9522,
        "beta1": 0.1657,
        "units": "mm",
        "notes": "THOR-05F AIS3+ IRF using max IR-TRACC deflection (X-Y resultant)."
    },

    # Diagnostic-only (not combined)
    "chest_A3ms": {
        "X50": 60.0,    # diagnostic placeholder
        "k": 0.08,      # diagnostic placeholder
        "units": "g",
        "notes": "Diagnostic-only placeholder; not combined in current calibration set."
    },

    # Femur/KTH AIS2+ proxy (logistic on femur axial force, kN)
    "femur_force_kN_AIS2plus_proxy": {
        "beta0": 5.7949,
        "beta1": -0.7619,
        "units": "kN",
        "notes": "Femur AIS2+ proxy risk using logistic model on femur axial force (kN)."
    }
}

# === UPGRADE NIJ: Mode-aware intercept structure (still configurable)
# True Nij uses mode-dependent intercepts (tension/compression and flexion/extension).
# If you don't have separate published values, keep these equal (as we do here) but the code is ready for replacement.
NECK_INTERCEPTS_MODES = {
    # Each entry: (F_int_N, M_int_Nm)
    "tension_flexion": (4287.0, 155.0),
    "tension_extension": (4287.0, 155.0),
    "compression_flexion": (4287.0, 155.0),
    "compression_extension": (4287.0, 155.0),
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
                 occupant_height: float = 1.75, # m
                 gender: str = "female",
                 is_pregnant: bool = False,

                 # Seating position parameters (affect injury risk)
                 seat_distance_from_wheel: float = 0.30,  # m
                 seat_recline_angle: float = 25.0,        # degrees from vertical
                 seat_height_relative_to_dash: float = 0.0,  # m
                 torso_length: float = None,              # m

                 # Occupant-specific vulnerabilities
                 neck_strength: str = "average",  # "weak", "average", "strong"
                 seat_position: str = "driver",    # "driver" or "passenger"
                 pelvis_lap_belt_fit: str = "average",  # "poor", "average", "good"

                 # Neck dynamic model parameters (upgrade Nij)
                 neck_nat_freq_hz: float = 10.0,      # Hz
                 neck_damping_ratio: float = 0.20,    # dimensionless
                 neck_k_override: float = None,       # N/m
                 neck_c_override: float = None,       # N*s/m

                 # Injury correlation tuning
                 injury_correlation_factor: float = DEFAULT_INJURY_CORRELATION_FACTOR,

                 # Restraint systems
                 seatbelt_used: bool = True,
                 seatbelt_pretensioner: bool = False,
                 seatbelt_load_limiter: bool = False,
                 front_airbag: bool = True,
                 side_airbag: bool = False,

                 # Structural parameters
                 crumple_zone_length: float = 0.5,  # m
                 cabin_rigidity: str = "medium",    # "low", "medium", "high"
                 intrusion: float = 0.0,            # m

                 # Optional biomechanical overrides
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

        # Neck dynamics
        self.neck_nat_freq_hz = float(neck_nat_freq_hz)
        self.neck_damping_ratio = float(neck_damping_ratio)
        self.neck_k_override = neck_k_override
        self.neck_c_override = neck_c_override

        # Correlated injury combination tuning
        self.injury_correlation_factor = float(injury_correlation_factor)

        # Restraints
        self.seatbelt_used = seatbelt_used
        self.seatbelt_pretensioner = seatbelt_pretensioner
        self.seatbelt_load_limiter = seatbelt_load_limiter
        self.front_airbag = front_airbag
        self.side_airbag = side_airbag

        # Vehicle/structure
        self.crumple_zone_length = crumple_zone_length
        self.cabin_rigidity = cabin_rigidity
        self.intrusion = intrusion

        # Biomechanical parameters scaled to occupant size
        self.head_mass = head_mass if head_mass is not None else self._calculate_head_mass()
        self.torso_mass = torso_mass if torso_mass is not None else self._calculate_torso_mass()
        self.leg_mass = leg_mass if leg_mass is not None else self._calculate_leg_mass()
        self.neck_lever_arm = neck_lever_arm if neck_lever_arm is not None else self._calculate_neck_lever_arm()

    def _calculate_head_mass(self) -> float:
        base_mass = self.occupant_mass * HEAD_MASS_FRACTION
        if self.gender == "female":
            base_mass *= 0.95
        return base_mass

    def _calculate_torso_mass(self) -> float:
        base_mass = self.occupant_mass * TORSO_MASS_FRACTION
        if self.is_pregnant:
            base_mass *= 1.15
        return base_mass

    def _calculate_leg_mass(self) -> float:
        return self.occupant_mass * LEG_MASS_FRACTION

    def _calculate_neck_lever_arm(self) -> float:
        height_scaling = self.occupant_height / REFERENCE_HEIGHT
        return REFERENCE_NECK_LEVER_ARM * height_scaling

    def _estimate_torso_length(self) -> float:
        return self.occupant_height * 0.34


class BaselineRiskCalculator:
    """
    Calculates baseline crash risk scores using physics-based injury criteria.
    """

    def __init__(self, inputs: CrashInputs):
        self.inputs = inputs
        self.results: Dict[str, Any] = {}

    @staticmethod
    def _normal_cdf(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    def _risk(self, criterion: str, value: float) -> float:
        params = RISK_CURVES[criterion]

        # Probit on log
        if params.get("form") == "probit_lognormal":
            X = float(value)
            if X <= 0.0:
                return 0.0
            mu = float(params["mu"])
            sigma = float(params["sigma"])
            z = (math.log(X) - mu) / sigma
            if z > 8.0:
                return 1.0
            if z < -8.0:
                return 0.0
            return float(self._normal_cdf(z))

        # Logistic regression
        if "beta0" in params and "beta1" in params:
            beta0 = float(params["beta0"])
            beta1 = float(params["beta1"])
            z = beta0 + beta1 * float(value)
            if z > 50.0:
                return 1.0
            if z < -50.0:
                return 0.0
            return 1.0 / (1.0 + math.exp(-z))

        # Legacy X50/k
        X50 = float(params["X50"])
        k = float(params["k"])
        exponent = -k * (float(value) - X50)
        if exponent > 50.0:
            return 0.0
        if exponent < -50.0:
            return 1.0
        return 1.0 / (1.0 + math.exp(exponent))

    def calculate_all(self) -> Dict[str, Any]:
        # Step 1: delta-V
        delta_v = self._compute_delta_v()

        # Step 2: pulse characteristics
        pulse_duration = self._get_pulse_duration()
        a_peak = self._compute_peak_acceleration(delta_v, pulse_duration)

        # Step 3: vehicle pulse
        time_array, a_vehicle, _a_vehicle_g = self._generate_crash_pulse(a_peak, pulse_duration)

        # Step 4: occupant pulse
        alpha = self._get_restraint_transfer_factor()
        a_occ = alpha * a_vehicle
        a_occ_g = a_occ / GRAVITY
        a_occ_peak = float(np.max(a_occ))

        # Step 5: injury criteria
        hic15 = self._compute_hic15(time_array, a_occ_g)

        # === UPGRADE NIJ: use time-history + head-neck dynamics instead of a_peak only
        nij, nij_details = self._compute_nij(time_array, a_occ)

        chest_a3ms = self._compute_chest_a3ms(time_array, a_occ_g)

        chest_deflection_m = self._compute_chest_deflection(a_occ_peak)
        chest_deflection_mm = chest_deflection_m * 1000.0

        femur_load_N = self._compute_femur_load(a_occ_peak)
        femur_force_kN = femur_load_N / 1000.0

        # Step 6: injury probabilities
        p_head = self._risk("head_HIC15_AIS3plus_probit", hic15)
        p_neck = self._risk("neck_Nij_AIS3plus", nij)
        p_thorax = self._risk("thorax_irtracc_max_deflection_mm_AIS3plus", chest_deflection_mm)
        p_chest_accel_diag = self._risk("chest_A3ms", chest_a3ms)
        p_femur = self._risk("femur_force_kN_AIS2plus_proxy", femur_force_kN)

        # Step 7: correlated combination (replaces independence)
        p_baseline, combo_details = self._combine_injury_probabilities_correlated(
            probabilities=[p_head, p_neck, p_thorax, p_femur],
            corr_factor=self.inputs.injury_correlation_factor,
            channel_names=["head", "neck", "thorax", "femur_proxy"],
        )
        risk_score = p_baseline * 100.0

        self.results = {
            "calibration_set": CALIBRATION_SET,

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

            # Nij upgraded outputs
            "Nij": round(nij, 3),
            "Nij_details": nij_details,

            # Diagnostic
            "chest_A3ms_g": round(chest_a3ms, 1),

            # Thorax proxy (m + mm)
            "thorax_deflection_proxy_m": round(chest_deflection_m, 5),
            "thorax_irtracc_max_deflection_proxy_mm": round(chest_deflection_mm, 1),

            # Femur
            "femur_load_kN": round(femur_force_kN, 1),

            # Injury probabilities
            "P_head": round(p_head, 4),
            "P_neck": round(p_neck, 4),
            "P_thorax_AIS3plus": round(p_thorax, 4),
            "P_chest_A3ms_diag": round(p_chest_accel_diag, 4),
            "P_femur_AIS2plus_proxy": round(p_femur, 4),

            # Combination
            "injury_combination_model": "correlation_adjusted_union",
            "injury_correlation_factor": round(self.inputs.injury_correlation_factor, 3),
            "injury_combination_details": combo_details,

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

            # Biomechanical parameters
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
                "Nij is computed from a simple head–neck spring-damper model driven by occupant acceleration time-history; this is still a proxy for true instrumented neck loads.",
                "Nij intercepts are mode-aware in code (tension/compression & flexion/extension) but currently share the same values unless you replace them with published mode-specific intercepts.",
                f"Neck injury adjusted for '{self.inputs.neck_strength}' neck strength and {self.inputs.seat_recline_angle}° recline",
                "Chest deflection from simplified spring model",
                f"Seat position: {self.inputs.seat_position} (passenger may have different posture/bracing)",
                f"Seat distance from wheel: {self.inputs.seat_distance_from_wheel} m (optimal: 0.25-0.30 m)",
                f"Pelvis/lap belt fit: {self.inputs.pelvis_lap_belt_fit} (affects load distribution and femur loading)",
                "Femur load from effective leg mass, adjusted for pelvis fit and seat position",
                "Thorax AIS3+ probability uses THOR-05F IR-TRACC max deflection IRF (X-Y resultant) on a proxy deflection signal (spring model).",
                "Chest 3ms acceleration is computed but treated as diagnostic only.",
                "Femur probability uses AIS2+ (KTH) proxy curve on femur axial force (kN); not AIS3+.",
                "Overall injury probability uses correlation-adjusted union (positive correlation reduces incremental risk compared to independence).",
                f"Correlation factor used: {self.inputs.injury_correlation_factor} (1.0 = independence; smaller = more clustering).",
            ]
        }

        return self.results

    # ================== Step 1: Delta-V Calculation ==================

    def _compute_delta_v(self) -> float:
        v0 = self.inputs.impact_speed
        e = self.inputs.coefficient_restitution
        return (1 + e) * v0

    # ================== Step 2: Crash Pulse Generation ==================

    def _get_pulse_duration(self) -> float:
        return PULSE_DURATIONS.get(self.inputs.crash_side, 0.10)

    def _compute_peak_acceleration(self, delta_v: float, T: float) -> float:
        return (math.pi / 2.0) * (delta_v / T)

    def _generate_crash_pulse(
        self,
        a_peak: float,
        T: float,
        sample_rate: int = 10000
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        n_samples = max(2, int(T * sample_rate))
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
        dt = float(time_array[1] - time_array[0])
        if dt <= 0.0:
            return 0.0
        max_window_samples = max(2, int(0.015 / dt))

        hic_max = 0.0
        for i in range(len(a_g) - 1):
            j_max = min(i + max_window_samples, len(a_g) - 1)
            for j in range(i + 1, j_max + 1):
                t1 = float(time_array[i])
                t2 = float(time_array[j])
                duration = t2 - t1
                if duration <= 0.0 or duration > 0.015:
                    continue
                avg_a = float(np.mean(a_g[i:j]))
                hic_value = duration * (avg_a ** 2.5)
                if hic_value > hic_max:
                    hic_max = hic_value
        return hic_max

    # === UPGRADE NIJ: dynamic, time-history, mode-aware structure
    def _compute_nij(self, time_array: np.ndarray, a_occ_mps2: np.ndarray) -> Tuple[float, Dict[str, Any]]:
        """
        Compute Nij using a simple head–neck SDOF dynamics model:

            m*ẍ + c*ẋ + k*x = -m*a_occ(t)

        where x is relative head displacement w.r.t. torso in the loading direction.
        Neck axial force proxy: Fz = k*x + c*ẋ
        Neck bending moment proxy: My = Fz * lever_arm (scaled) * recline_factor

        Then compute Nij over time with mode-aware intercept selection.
        Return the peak Nij.
        """
        t = time_array
        a = a_occ_mps2

        if len(t) < 2:
            return 0.0, {"note": "Insufficient time samples for Nij dynamics."}

        dt = float(t[1] - t[0])
        if dt <= 0.0:
            return 0.0, {"note": "Non-positive dt; cannot compute Nij dynamics."}

        m = float(self.inputs.head_mass)

        # Determine k, c from natural frequency + damping ratio unless overridden
        if self.inputs.neck_k_override is not None:
            k = float(self.inputs.neck_k_override)
        else:
            wn = 2.0 * math.pi * max(0.1, float(self.inputs.neck_nat_freq_hz))  # rad/s
            k = m * (wn ** 2)

        if self.inputs.neck_c_override is not None:
            c = float(self.inputs.neck_c_override)
        else:
            zeta = max(0.0, float(self.inputs.neck_damping_ratio))
            c = 2.0 * zeta * math.sqrt(max(1e-9, k * m))

        # Integrate using semi-implicit (symplectic-ish) Euler for stability
        x = 0.0     # relative displacement (m)
        v = 0.0     # relative velocity (m/s)

        lever_arm = float(self.inputs.neck_lever_arm)
        recline_factor = 1.0 + (float(self.inputs.seat_recline_angle) / 100.0)

        # Strength multipliers (kept from your design)
        strength_multipliers = {
            "weak": 1.3,
            "average": 1.0,
            "strong": 0.85
        }
        strength_mult = strength_multipliers.get(self.inputs.neck_strength, 1.0)

        nij_peak = 0.0
        nij_peak_components = {"Fz_N": 0.0, "My_Nm": 0.0, "mode": "unknown"}
        mode_counts = {"tension_flexion": 0, "tension_extension": 0, "compression_flexion": 0, "compression_extension": 0}

        for i in range(len(t)):
            # Relative acceleration from SDOF equation:
            # ẍ = -(c*v + k*x)/m - a_occ(t)
            xdd = (-(c * v + k * x) / m) - float(a[i])

            # semi-implicit Euler
            v = v + xdd * dt
            x = x + v * dt

            # Neck force/moment proxies
            Fz = (k * x) + (c * v)                     # N (proxy)
            My = Fz * lever_arm * recline_factor       # N*m (proxy)

            # Determine mode based on signs
            # Convention here:
            #   tension: Fz >= 0
            #   compression: Fz < 0
            #   flexion vs extension: use sign of My (proxy sign convention)
            if Fz >= 0.0 and My >= 0.0:
                mode = "tension_flexion"
            elif Fz >= 0.0 and My < 0.0:
                mode = "tension_extension"
            elif Fz < 0.0 and My >= 0.0:
                mode = "compression_flexion"
            else:
                mode = "compression_extension"

            mode_counts[mode] += 1

            F_int, M_int = NECK_INTERCEPTS_MODES[mode]

            # Nij definition (proxy): Nij = Fz/Fint + My/Mint
            nij_t = (Fz / float(F_int)) + (My / float(M_int))
            nij_t *= strength_mult

            if nij_t > nij_peak:
                nij_peak = float(nij_t)
                nij_peak_components = {"Fz_N": float(Fz), "My_Nm": float(My), "mode": mode}

        details = {
            "model": "head_neck_sdof_proxy",
            "dt_s": dt,
            "m_head_kg": m,
            "k_neck_N_per_m": k,
            "c_neck_Ns_per_m": c,
            "lever_arm_m": lever_arm,
            "recline_factor": recline_factor,
            "strength_multiplier": strength_mult,
            "nij_peak_components": nij_peak_components,
            "mode_counts": mode_counts,
            "notes": [
                "This is a proxy Nij computed from a head–neck SDOF response driven by occupant translational acceleration.",
                "Replace NECK_INTERCEPTS_MODES with published mode-specific intercepts when available.",
                "If you later have neck load channels (Fz/My), replace the SDOF proxy with direct computation."
            ]
        }
        return nij_peak, details

    def _compute_chest_a3ms(self, time_array: np.ndarray, a_g: np.ndarray) -> float:
        dt = float(time_array[1] - time_array[0])
        if dt <= 0.0:
            return 0.0
        window_samples = max(1, int(0.003 / dt))
        max_avg = 0.0
        for i in range(len(a_g) - window_samples):
            avg_a = float(np.mean(a_g[i:i + window_samples]))
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

    # ================== Step 6: Overall Risk Combination ==================

    # === NEW: correlation-adjusted union model
    def _combine_injury_probabilities_correlated(
        self,
        probabilities: List[float],
        corr_factor: float = DEFAULT_INJURY_CORRELATION_FACTOR,
        channel_names: List[str] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Correlation-adjusted union probability for positively correlated injury channels.

        Independence:
            P(any) = 1 - Π(1 - p_i)

        Positive correlation (injuries cluster) -> union grows more slowly.
        A simple, tunable adjustment:
            P(any) = 1 - ( Π(1 - p_i) )^(corr_factor)

        Properties:
          - corr_factor = 1.0 => independence
          - corr_factor < 1.0 => more positive correlation => higher P(none) => lower union than independence
          - corr_factor > 1.0 would imply negative correlation (not typical here), so we clamp to [0.1, 1.0]

        Returns:
          (p_any, details)
        """
        if channel_names is None:
            channel_names = [f"ch{i}" for i in range(len(probabilities))]

        probs = [min(1.0, max(0.0, float(p))) for p in probabilities]
        cf = float(corr_factor)
        cf = min(1.0, max(0.1, cf))

        # compute log of product to avoid underflow
        log_p_none_ind = 0.0
        for p in probs:
            log_p_none_ind += math.log(max(1e-12, 1.0 - p))

        p_none_ind = math.exp(log_p_none_ind)
        p_none_corr = p_none_ind ** cf
        p_any_corr = 1.0 - p_none_corr

        details = {
            "channels": [{"name": n, "p": float(p)} for n, p in zip(channel_names, probs)],
            "p_none_independence": float(p_none_ind),
            "p_any_independence": float(1.0 - p_none_ind),
            "corr_factor_used": float(cf),
            "p_none_corr_adjusted": float(p_none_corr),
            "p_any_corr_adjusted": float(p_any_corr),
            "notes": [
                "This is a simple positive-correlation adjustment (not a full copula/joint model).",
                "Tune corr_factor using real crash-test outcomes: fit corr_factor to match observed multi-region injury rates."
            ]
        }
        return p_any_corr, details


# ================== Convenience Functions ==================

def calculate_baseline_risk(inputs: CrashInputs) -> Dict[str, Any]:
    calculator = BaselineRiskCalculator(inputs)
    return calculator.calculate_all()


def format_results_for_gemini(results: Dict[str, Any]) -> str:
    lines = [
        "=== BASELINE CRASH RISK CALCULATION RESULTS ===",
        "",
        f"CALIBRATION SET: {results.get('calibration_set','unknown')}",
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
        f"  Nij (dynamic proxy): {results['Nij']}",
        f"  Chest 3ms clip (diagnostic): {results['chest_A3ms_g']} g",
        f"  Thorax deflection proxy (IR-TRACC max, mm): {results['thorax_irtracc_max_deflection_proxy_mm']} mm",
        f"  Femur axial force (kN): {results['femur_load_kN']} kN",
        "",
        "INJURY PROBABILITIES:",
        f"  Head AIS3+: {results['P_head']*100:.2f}%",
        f"  Neck AIS3+: {results['P_neck']*100:.2f}%",
        f"  Thorax AIS3+: {results['P_thorax_AIS3plus']*100:.2f}%",
        f"  Femur AIS2+ proxy: {results['P_femur_AIS2plus_proxy']*100:.2f}%",
        "",
        "COMBINATION MODEL:",
        f"  Model: {results.get('injury_combination_model','unknown')}",
        f"  Correlation factor: {results.get('injury_correlation_factor','?')}",
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

    for assumption in results.get("assumptions", []):
        lines.append(f"  - {assumption}")

    return "\n".join(lines)
