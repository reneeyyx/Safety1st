from typing import List

RELEVANT_KEYWORDS = [
    "female",
    "women",
    "woman",
    "pregnant",
    "5th percentile",
    "small female",
    "stature",
    "seatbelt",
    "seat belt",
    "airbag",
    "air bag",
    "crumple zone",
    "cabin rigidity",
    "driver",
    "passenger",
    "dummy",
]


def filter_relevant_paragraphs(text: str) -> List[str]:
    if not text:
        return []

    # simple sentence-ish split
    raw_segments = [seg.strip() for seg in text.split(". ") if seg.strip()]
    relevant: List[str] = []

    for seg in raw_segments:
        lower_seg = seg.lower()
        if any(keyword in lower_seg for keyword in RELEVANT_KEYWORDS):
            relevant.append(seg)

    # cap to avoid huge payloads
    return relevant[:20]