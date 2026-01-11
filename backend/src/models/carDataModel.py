"""
Car/Vehicle data model for crash risk calculation.
Validates vehicle and crash parameters.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal


class CarDataModel(BaseModel):
    """
    Vehicle and crash configuration parameters.
    Uses user-friendly units (km/h, cm) which get converted to SI units.
    """

    # ==================== Crash Parameters ====================
    impact_speed_kmh: float = Field(
        ...,
        ge=0,
        le=200,
        description="Impact speed in km/h (0-200)"
    )

    crash_side: Literal["frontal", "left", "right"] = Field(
        ...,
        description="Side of crash: frontal, left, or right"
    )

    # ==================== Vehicle Parameters ====================
    vehicle_mass_kg: float = Field(
        ...,
        ge=500,
        le=5000,
        description="Vehicle mass in kg (500-5000)"
    )

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

    airbag_capacity_liters: Optional[float] = Field(
        default=60.0,
        ge=20,
        le=150,
        description="Airbag capacity in liters (20-150L). Typical: 35L (compact), 60L (standard), 80-100L (large). Optimal is ~0.9L per kg of occupant mass."
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

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
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
            }
        }


class CarParameters:
    """
    Lightweight car parameters model for scraper.
    Simpler interface than CarDataModel (no validation).
    """
    def __init__(self,
                 crash_side: str,
                 vehicle_mass: float,
                 crumple_zone_length: float,
                 cabin_rigidity: str,
                 seatbelt_pretensioner: bool,
                 seatbelt_load_limiter: bool,
                 front_airbags: bool,
                 side_airbags: bool):
        self.crash_side = crash_side
        self.vehicle_mass = vehicle_mass
        self.crumple_zone_length = crumple_zone_length
        self.cabin_rigidity = cabin_rigidity
        self.seatbelt_pretensioner = seatbelt_pretensioner
        self.seatbelt_load_limiter = seatbelt_load_limiter
        self.front_airbags = front_airbags
        self.side_airbags = side_airbags
