"""Test script for the scraper module"""
import asyncio
import sys
import os

# Add src to path so we can import modules
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

from models.carDataModel import CarParameters
from models.dummyDataModel import DummyDetails
from scraper import scrape_safety_data


async def test_scraper():
    """Test the scraper with sample data"""

    # Create test car parameters
    car = CarParameters(
        crash_side="frontal",
        vehicle_mass=1500,
        crumple_zone_length=0.8,
        cabin_rigidity="med",
        seatbelt_pretensioner=True,
        seatbelt_load_limiter=True,
        front_airbags=True,
        side_airbags=False
    )

    # Create test dummy details
    dummy = DummyDetails(
        gender="female",
        seat_position="driver",
        pregnant=True
    )

    print("Testing scraper with:")
    print(f"  Car: {car.crash_side} crash, {car.vehicle_mass}kg")
    print(f"  Dummy: {dummy.gender}, pregnant={dummy.pregnant}")
    print()

    # Run scraper
    result = await scrape_safety_data(car, dummy)

    print("Scraper result:")
    print(f"  Summary: {result['summaryText'][:200]}...")
    print(f"  Gender bias notes: {len(result['genderBiasNotes'])} notes")
    print(f"  Data sources: {len(result['dataSources'])} sources")
    print()

    if result['genderBiasNotes']:
        print("Gender bias notes:")
        for note in result['genderBiasNotes']:
            print(f"  - {note[:100]}...")


if __name__ == "__main__":
    asyncio.run(test_scraper())
