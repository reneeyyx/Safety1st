"""
Pydantic models for crash risk calculation API requests.
Validates user form input and provides type safety.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal


class CrashRequestModel(BaseModel):
    """
    Request model for crash risk calculation endpoint.

    Uses user-friendly units (km/h, cm) which get converted to SI units (m/s, m)
    before passing to the calculator.
    """

    # ==================== Vehicle/Crash Parameters ====================
    impact_speed_kmh: float = Field(
        ...,
        ge=0,
        le=200,
        description="Impact speed in km/h (0-200)"
    )

    vehicle_mass_kg: float = Field(
        ...,
        ge=500,
        le=5000,
        description="Vehicle mass in kg (500-5000)"
    )

    crash_side: Literal["frontal", "side", "rear"] = Field(
        ...,
        description="Side of crash: frontal, side, or rear"
    )

    # ==================== Occupant Parameters ====================
    occupant_mass_kg: float = Field(
        ...,
        ge=40,
        le=150,
        description="Occupant body mass in kg (40-150)"
    )

    occupant_height_m: float = Field(
        ...,
        ge=1.4,
        le=2.1,
        description="Occupant height in meters (1.4-2.1)"
    )

    gender: Literal["male", "female"] = Field(
        ...,
        description="Occupant gender"
    )

    is_pregnant: bool = Field(
        default=False,
        description="Is occupant pregnant? (affects torso mass and injury risk)"
    )

    # ==================== Seating Position Parameters ====================
    seat_distance_from_wheel_cm: Optional[float] = Field(
        default=30.0,
        ge=10,
        le=80,
        description="Distance from steering wheel/dash in cm (optimal: 25-30)"
    )

    seat_recline_angle_deg: Optional[float] = Field(
        default=25.0,
        ge=0,
        le=60,
        description="Seat recline angle from vertical in degrees (0=upright, 45=reclined)"
    )

    seat_height_relative_to_dash_cm: Optional[float] = Field(
        default=0.0,
        ge=-15,
        le=20,
        description="Seat height relative to dashboard in cm (negative=below, positive=above)"
    )

    neck_strength: Optional[Literal["weak", "average", "strong"]] = Field(
        default="average",
        description="Neck strength (weak=elderly/injured, average=normal, strong=athletic)"
    )

    # ==================== Restraint Systems ====================
    seatbelt_used: bool = Field(
        default=True,
        description="Is seatbelt worn?"
    )

    seatbelt_pretensioner: bool = Field(
        default=False,
        description="Does vehicle have seatbelt pretensioner?"
    )

    seatbelt_load_limiter: bool = Field(
        default=False,
        description="Does vehicle have seatbelt load limiter?"
    )

    front_airbag: bool = Field(
        default=True,
        description="Is front airbag present?"
    )

    side_airbag: bool = Field(
        default=False,
        description="Is side airbag present?"
    )

    # ==================== Vehicle Structure Parameters ====================
    crumple_zone_length_m: Optional[float] = Field(
        default=0.5,
        ge=0.1,
        le=1.0,
        description="Crumple zone length in meters (0.1-1.0)"
    )

    cabin_rigidity: Optional[Literal["low", "medium", "high"]] = Field(
        default="medium",
        description="Cabin structural rigidity"
    )

    intrusion_cm: Optional[float] = Field(
        default=0.0,
        ge=0,
        le=50,
        description="Cabin intrusion distance in cm (important for side impacts)"
    )

    # ==================== Validators ====================

    @field_validator('impact_speed_kmh')
    @classmethod
    def validate_speed(cls, v: float) -> float:
        """Validate impact speed is within reasonable range."""
        if v < 0:
            raise ValueError('Impact speed cannot be negative')
        if v > 200:
            raise ValueError('Impact speed exceeds maximum (200 km/h)')
        return v

    @field_validator('occupant_mass_kg')
    @classmethod
    def validate_mass(cls, v: float) -> float:
        """Validate occupant mass is within reasonable range."""
        if v < 40:
            raise ValueError('Occupant mass too low (minimum 40 kg)')
        if v > 150:
            raise ValueError('Occupant mass too high (maximum 150 kg)')
        return v

    @field_validator('occupant_height_m')
    @classmethod
    def validate_height(cls, v: float) -> float:
        """Validate occupant height is within reasonable range."""
        if v < 1.4:
            raise ValueError('Occupant height too low (minimum 1.4 m)')
        if v > 2.1:
            raise ValueError('Occupant height too high (maximum 2.1 m)')
        return v

    @field_validator('seat_distance_from_wheel_cm')
    @classmethod
    def validate_seat_distance(cls, v: Optional[float]) -> Optional[float]:
        """Validate seat distance and warn if suboptimal."""
        if v is None:
            return v
        if v < 15:
            # Note: Warning will be added to response, not blocking validation
            pass  # Too close to airbag
        elif v > 50:
            pass  # Too far from airbag
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "impact_speed_kmh": 50.0,
                "vehicle_mass_kg": 1500.0,
                "crash_side": "frontal",
                "occupant_mass_kg": 75.0,
                "occupant_height_m": 1.75,
                "gender": "male",
                "is_pregnant": False,
                "seat_distance_from_wheel_cm": 30.0,
                "seat_recline_angle_deg": 25.0,
                "seat_height_relative_to_dash_cm": 0.0,
                "neck_strength": "average",
                "seatbelt_used": True,
                "seatbelt_pretensioner": True,
                "seatbelt_load_limiter": True,
                "front_airbag": True,
                "side_airbag": False,
                "crumple_zone_length_m": 0.6,
                "cabin_rigidity": "medium",
                "intrusion_cm": 0.0
            }
        }
