from bs4 import BeautifulSoup
from typing import List


def extract_text(html: str) -> str:
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # remove scripts/styles/noscript
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # For bibliography/research pages, we need to extract from multiple elements
    # Not just <p> tags, but also <div>, <span>, <li>, <td> that contain text
    text_elements: List[str] = []

    # Get paragraphs (primary)
    for p in soup.find_all("p"):
        text = p.get_text(separator=" ", strip=True)
        if len(text) > 20:  # Filter out very short snippets
            text_elements.append(text)

    # Get divs with substantial text (for research pages)
    for div in soup.find_all("div", class_=True):
        text = div.get_text(separator=" ", strip=True)
        # Only include if it has substantial content and doesn't duplicate
        if len(text) > 50 and text not in text_elements:
            text_elements.append(text)

    # Get list items (often used in research summaries)
    for li in soup.find_all("li"):
        text = li.get_text(separator=" ", strip=True)
        if len(text) > 30 and text not in text_elements:
            text_elements.append(text)

    # Get table cells (sometimes research data is in tables)
    for td in soup.find_all("td"):
        text = td.get_text(separator=" ", strip=True)
        if len(text) > 30 and text not in text_elements:
            text_elements.append(text)

    # If nothing found, try getting all text from body
    if not text_elements:
        body = soup.find("body")
        if body:
            text = body.get_text(separator=" ", strip=True)
            return text

    return " ".join(text_elements)
