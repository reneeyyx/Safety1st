from typing import List
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.carDataModel import CarParameters
from models.dummyDataModel import DummyDetails


def build_search_query(car: CarParameters, dummy: DummyDetails) -> str:
    """Build a search query based on car and dummy parameters"""
    crash_side = car.crash_side

    gender_words: List[str] = []
    if dummy.gender == "female":
        gender_words.append("female")
    if dummy.pregnant:
        gender_words.append("pregnant")

    crash_words: List[str] = []
    if crash_side == "frontal":
        crash_words.append("frontal crash test")
    else:
        crash_words.append("side impact crash test")

    restraint_words: List[str] = []
    if not car.side_airbags and crash_side != "frontal":
        restraint_words.append("side airbags injury risk")
    if not car.front_airbags and crash_side == "frontal":
        restraint_words.append("airbag injury risk")
    if not car.seatbelt_load_limiter:
        restraint_words.append("seatbelt load limiter injury")
    if not car.seatbelt_pretensioner:
        restraint_words.append("seatbelt pretensioner injury")

    extra_words: List[str] = [
        "female vs male injury risk",
        "crash test dummy",
        "small female occupant",
    ]

    query_parts = crash_words + gender_words + restraint_words + extra_words

    if not query_parts:
        return "crash injury risk female vs male"

    return " ".join(query_parts)


async def search_urls(query: str) -> List[str]:
    """
    Returns curated URLs from crash test safety organizations.

    These URLs contain real crash test data, gender-specific injury statistics,
    and safety feature effectiveness research.
    """
    # Real crash safety data sources
    SAFETY_URLS = [
        # IIHS gender fatality statistics
        "https://www.iihs.org/topics/fatality-statistics/detail/gender",

        # NHTSA crash test ratings
        "https://www.nhtsa.gov/ratings",

        # Research on female crash test dummies and injury disparities
        "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5001799/",

        # IIHS frontal crash test info
        "https://www.iihs.org/ratings/about/frontal-crash-tests",

        # IIHS side crash test info
        "https://www.iihs.org/ratings/about/side-crash-tests",
    ]

    return SAFETY_URLS