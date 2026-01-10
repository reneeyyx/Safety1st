"""
Dummy/Occupant data model for crash risk calculation.
Validates occupant and seating parameters.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal


class DummyDataModel(BaseModel):
    """
    Occupant (crash test dummy) parameters and seating position.
    Uses user-friendly units (cm) which get converted to SI units.
    """

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

    # ==================== Validators ====================

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
            pass  # Too close to airbag - warning in response
        elif v > 50:
            pass  # Too far from airbag - warning in response
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "occupant_mass_kg": 75.0,
                "occupant_height_m": 1.75,
                "gender": "male",
                "is_pregnant": False,
                "seat_distance_from_wheel_cm": 30.0,
                "seat_recline_angle_deg": 25.0,
                "seat_height_relative_to_dash_cm": 0.0,
                "neck_strength": "average"
            }
        }
