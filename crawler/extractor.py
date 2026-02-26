"""
extractor.py — Cleans HTML pages and extracts meaningful text.

Strips navigation, footers, scripts, styles, and returns only
the content-bearing text of a page.
"""

import requests
from bs4 import BeautifulSoup


# Tags that typically contain boilerplate, not content
NOISE_TAGS = [
    "nav", "footer", "header", "script", "style", "noscript",
    "aside", "form", "iframe", "svg", "button",
]

NOISE_CLASSES = [
    "navbar", "footer", "sidebar", "menu", "breadcrumb",
    "advertisement", "ad", "cookie", "popup",
]


def extract_text_from_html(url: str) -> dict | None:
    """
    Fetches a URL and returns a dict with:
      - url: source URL
      - title: page <title>
      - content: cleaned body text
    Returns None if the fetch fails or yields no content.
    """
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        })
        resp.raise_for_status()
    except Exception as e:
        print(f"  [ERROR] HTML extraction failed for {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # Remove noise tags
    for tag_name in NOISE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove elements with noisy class names
    for cls in NOISE_CLASSES:
        for tag in soup.find_all(class_=lambda c: c and cls in str(c).lower()):
            tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text(strip=True)
    else:
        title = url

    body = soup.find("body")
    text = body.get_text(separator="\n", strip=True) if body else soup.get_text(separator="\n", strip=True)

    # Collapse excessive whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    clean_text = "\n".join(lines)

    # Skip pages with very little content (likely error pages or redirects)
    if len(clean_text) < 50:
        print(f"  [SKIP] Too little content ({len(clean_text)} chars): {url}")
        return None

    return {
        "url": url,
        "title": title,
        "content": clean_text,
        "type": "html",
    }
