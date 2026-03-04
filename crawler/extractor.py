"""
extractor.py — Cleans HTML pages and extracts meaningful text.

Strips navigation, footers, scripts, styles, and returns only
the content-bearing text of a page. Retries on timeout.
"""

import requests
from bs4 import BeautifulSoup
import time


# Tags that typically contain boilerplate, not content
NOISE_TAGS = [
    "nav", "footer", "script", "style", "noscript",
    "iframe", "svg",
]

NOISE_CLASSES = [
    "navbar", "footer", "sidebar", "menu", "breadcrumb",
    "advertisement", "ad", "cookie", "popup",
]

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
})


def extract_text_from_html(url: str) -> dict | None:
    """
    Fetches a URL and returns a dict with:
      - url: source URL
      - title: page <title>
      - content: cleaned body text
    Returns None if the fetch fails or yields no content.
    """
    resp = None
    for attempt in range(3):
        try:
            resp = SESSION.get(url, timeout=30, allow_redirects=True)
            resp.raise_for_status()
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
                continue
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

    # Accept any page with content (even small ones — they may have useful titles/metadata)
    if len(clean_text) < 10:
        print(f"  [SKIP] Empty page ({len(clean_text)} chars): {url}")
        return None

    return {
        "url": url,
        "title": title,
        "content": clean_text,
        "type": "html",
    }
