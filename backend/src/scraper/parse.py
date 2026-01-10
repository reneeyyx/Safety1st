from bs4 import BeautifulSoup


def extract_text(html: str) -> str:
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # remove scripts/styles/noscript
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # collect paragraph text
    paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
    text = " ".join(paragraphs)
    return text
