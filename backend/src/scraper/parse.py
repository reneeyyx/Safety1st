from bs4 import BeautifulSoup
from typing import List


def extract_text(html: str) -> str:
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # remove scripts/styles/noscript/nav/footer/header
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
        tag.decompose()

    text_elements: List[str] = []

    # IIHS bibliography pages use specific structure:
    # Look for citation/reference containers first
    citation_containers = soup.find_all(['div', 'section', 'article'],
                                       class_=lambda x: x and any(term in str(x).lower()
                                       for term in ['citation', 'reference', 'content', 'main', 'article', 'bibliography']))

    if citation_containers:
        # Extract from specific bibliography containers
        for container in citation_containers:
            # Get title/heading
            for heading in container.find_all(['h1', 'h2', 'h3', 'h4']):
                text = heading.get_text(separator=" ", strip=True)
                if len(text) > 10:
                    text_elements.append(text)

            # Get paragraphs within container
            for p in container.find_all("p"):
                text = p.get_text(separator=" ", strip=True)
                if len(text) > 30:
                    text_elements.append(text)

            # Get any direct text in container
            for child in container.find_all(['span', 'div'], recursive=False):
                text = child.get_text(separator=" ", strip=True)
                if len(text) > 40 and not any(text in existing for existing in text_elements):
                    text_elements.append(text)

    # Fallback: Get all paragraphs
    if not text_elements:
        for p in soup.find_all("p"):
            text = p.get_text(separator=" ", strip=True)
            if len(text) > 20:
                text_elements.append(text)

    # Fallback: Get main content area
    if not text_elements:
        main_content = soup.find(['main', 'article', 'div'], id=lambda x: x and 'content' in str(x).lower())
        if main_content:
            text = main_content.get_text(separator=" ", strip=True)
            if len(text) > 100:
                return text

    # Last resort: Get all body text
    if not text_elements:
        body = soup.find("body")
        if body:
            text = body.get_text(separator=" ", strip=True)
            return text

    return " ".join(text_elements)
