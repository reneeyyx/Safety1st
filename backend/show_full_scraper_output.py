"""
Show full scraper output without truncation.

This script demonstrates how to see complete scraped data
instead of the truncated "..." output from test scripts.

Usage:
    python show_full_scraper_output.py
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from models.carDataModel import CarParameters
from models.dummyDataModel import DummyDetails
from scraper import scrape_safety_data


async def show_full_data():
    """Scrape data and display complete results (no truncation)"""

    print("\n" + "="*80)
    print("SAFETY DATA SCRAPER - FULL OUTPUT (NO TRUNCATION)")
    print("="*80 + "\n")

    # Configure scraper parameters
    car = CarParameters(
        crash_side="frontal",
        vehicle_mass=1500,
        crumple_zone_length=0.6,
        cabin_rigidity="medium",
        seatbelt_pretensioner=True,
        seatbelt_load_limiter=True,
        front_airbags=True,
        side_airbags=False
    )

    dummy = DummyDetails(
        gender="female",
        seat_position="driver",
        pregnant=False,
        pelvis_lap_belt_fit="average"
    )

    print("Scraping with parameters:")
    print(f"  Crash: {car.crash_side}")
    print(f"  Gender: {dummy.gender}")
    print(f"  Pregnant: {dummy.pregnant}")
    print(f"  Seat: {dummy.seat_position}")
    print("\nFetching data from safety organizations...")
    print("(This may take 5-15 seconds)\n")

    # Run scraper
    result = await scrape_safety_data(car, dummy)

    # Display full summary text (NO truncation)
    print("="*80)
    print("FULL SUMMARY TEXT")
    print("="*80)
    print(result['summaryText'])
    print()

    # Display full gender bias notes (NO truncation)
    print("="*80)
    print("FULL GENDER BIAS NOTES")
    print("="*80)
    if result['genderBiasNotes']:
        for i, note in enumerate(result['genderBiasNotes'], 1):
            print(f"\n{i}. {note}")
    else:
        print("(No gender-specific notes found)")
    print()

    # Display data sources
    print("="*80)
    print("DATA SOURCES")
    print("="*80)
    if result['dataSources']:
        for source in result['dataSources']:
            print(f"  - {source}")
        print(f"\nTotal sources scraped: {len(result['dataSources'])}")
    else:
        print("(No data sources successfully scraped)")
    print()

    # Statistics
    print("="*80)
    print("STATISTICS")
    print("="*80)
    print(f"Summary text length: {len(result['summaryText'])} characters")
    print(f"Gender bias notes: {len(result['genderBiasNotes'])} notes")
    print(f"Data sources: {len(result['dataSources'])} URLs")
    print()

    print("="*80)
    print("SCRAPING COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(show_full_data())
