from typing import List, TypedDict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.carDataModel import CarParameters
from models.dummyDataModel import DummyDetails
from utils import logger

from .search import build_search_query, search_urls
from .fetch import fetch_html
from .parse import extract_text
from .filter import filter_relevant_paragraphs


class ScrapedContext(TypedDict):
    summaryText: str
    genderBiasNotes: List[str]
    dataSources: List[str]


async def scrape_safety_data(
    car: CarParameters,
    dummy: DummyDetails,
) -> ScrapedContext:
    """
    Main entry point for the webscraper.

    Given the car and dummy parameters, it:
    1) builds a search query
    2) gets candidate URLs
    3) fetches HTML
    4) extracts and filters relevant text
    5) returns a compact context object for Gemini
    """
    query = build_search_query(car, dummy)
    logger.info("Scraper query:", query)

    urls = await search_urls(query)
    logger.info("Scraper URLs:", urls)

    all_paragraphs: List[str] = []
    data_sources: List[str] = []

    for url in urls:
        html = await fetch_html(url)
        if not html:
            continue

        text = extract_text(html)
        relevant_segments = filter_relevant_paragraphs(text)

        if relevant_segments:
            all_paragraphs.extend(relevant_segments)
            data_sources.append(url)

    # if nothing found, return a generic but useful context
    if not all_paragraphs:
        summary_text = (
            "No specific external crash data matched this query; relying on baseline "
            "safety knowledge and well-known gender bias trends in crash testing."
        )
        gender_bias_notes = [
            "Female occupants, especially smaller and pregnant women, have historically faced higher "
            "injury risk because many crash tests and restraint systems are tuned to an average male body.",
        ]
        return {
            "summaryText": summary_text,
            "genderBiasNotes": gender_bias_notes,
            "dataSources": [],
        }

    # build a short summary string from first few relevant segments
    summary_text = " ".join(all_paragraphs[:5])

    # pull out a few paragraphs that explicitly mention female / women / pregnant
    gender_bias_notes = [
        p
        for p in all_paragraphs
        if any(word in p.lower() for word in ["female", "women", "woman", "pregnant"])
    ][:3]

    if not gender_bias_notes:
        gender_bias_notes = [
            "External sources discuss crash injury risk, but explicit female-focused statistics in this query were limited."
        ]

    return {
        "summaryText": summary_text,
        "genderBiasNotes": gender_bias_notes,
        "dataSources": data_sources,
    }