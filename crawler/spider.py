"""
spider.py — The "Spider" that crawls the YCCE domain.

Supports two modes:
 1. Sitemap mode (default): Parses a local sitemap.xml file to extract ALL URLs.
 2. BFS fallback: If no sitemap, crawls links starting from the YCCE root page.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import config
import time
import os
import xml.etree.ElementTree as ET


def _get_base_domain(netloc: str) -> str:
    """Strip 'www.' prefix to normalize domain comparison."""
    return netloc.lower().replace("www.", "")


def _load_sitemap(sitemap_path: str) -> tuple[set[str], set[str]]:
    """
    Parse sitemap.xml and return (page_urls, pdf_urls).
    Skips .doc, .docx, image files, and other non-content URLs.
    """
    tree = ET.parse(sitemap_path)
    root = tree.getroot()

    # Handle XML namespace
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    page_urls = set()
    pdf_urls = set()

    # Extensions to skip (not useful content)
    skip_extensions = {".doc", ".docx", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".mp4", ".mp3", ".zip"}

    for url_elem in root.findall("sm:url", ns):
        loc = url_elem.find("sm:loc", ns)
        if loc is None or not loc.text:
            continue

        url = loc.text.strip()

        # Skip non-content files
        lower_url = url.lower()
        ext = os.path.splitext(urlparse(lower_url).path)[1]
        if ext in skip_extensions:
            continue

        if lower_url.endswith(".pdf"):
            if len(pdf_urls) < config.MAX_PDFS:
                pdf_urls.add(url)
        else:
            if len(page_urls) < config.MAX_PAGES:
                page_urls.add(url)

    return page_urls, pdf_urls


def crawl(seed_url: str = None) -> tuple[set[str], set[str]]:
    """
    Main entry point. Uses sitemap.xml if available, falls back to BFS crawl.
    Returns (page_urls, pdf_urls).
    """
    # Check for local sitemap.xml
    sitemap_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sitemap.xml")

    if os.path.exists(sitemap_path):
        print(f"[CRAWL] Found sitemap at: {sitemap_path}")
        page_urls, pdf_urls = _load_sitemap(sitemap_path)
        print(f"[CRAWL] Loaded from sitemap: {len(page_urls)} pages, {len(pdf_urls)} PDFs")
        return page_urls, pdf_urls
    else:
        print("[CRAWL] No sitemap.xml found. Falling back to BFS crawl.")
        return _bfs_crawl(seed_url)


def _bfs_crawl(seed_url: str = None) -> tuple[set[str], set[str]]:
    """
    BFS crawl starting from `seed_url`.
    Returns (page_urls, pdf_urls).
    """
    seed = seed_url or config.TARGET_DOMAIN
    base_domain = _get_base_domain(urlparse(seed).netloc)

    visited: set[str] = set()
    page_urls: set[str] = set()
    pdf_urls: set[str] = set()
    queue: deque[str] = deque([seed])

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    })

    print(f"[CRAWL] Starting crawl from: {seed}")
    print(f"[CRAWL] Base domain: {base_domain}")

    while queue:
        if len(page_urls) >= config.MAX_PAGES and len(pdf_urls) >= config.MAX_PDFS:
            print("[CRAWL] Reached max limits for pages and PDFs. Stopping.")
            break

        url = queue.popleft()

        # Normalize: strip fragment, trailing slash
        url = url.split("#")[0].rstrip("/")

        # Skip invalid URLs
        if not url.startswith("http"):
            continue

        if url in visited:
            continue
        visited.add(url)

        parsed = urlparse(url)

        # Only follow links within the same base domain
        if _get_base_domain(parsed.netloc) != base_domain:
            continue

        # Check if it's a PDF link
        if url.lower().endswith(".pdf"):
            if len(pdf_urls) < config.MAX_PDFS:
                pdf_urls.add(url)
                print(f"  [PDF {len(pdf_urls)}] {url}")
            continue

        if len(page_urls) >= config.MAX_PAGES:
            continue

        # Fetch the page
        try:
            resp = session.get(url, timeout=15, allow_redirects=True)
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                continue
            resp.raise_for_status()
        except Exception as e:
            print(f"  [ERROR] {url}: {e}")
            continue

        page_urls.add(url)
        print(f"  [PAGE {len(page_urls)}] {url}")

        # Parse links
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()

            # Skip javascript:, mailto:, tel: links
            if href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue

            full_url = urljoin(url, href)

            # Only queue links within the same base domain
            link_domain = _get_base_domain(urlparse(full_url).netloc)
            if link_domain == base_domain:
                queue.append(full_url)

        # Be polite
        time.sleep(0.3)

    print(f"\n[CRAWL] Complete: {len(page_urls)} pages, {len(pdf_urls)} PDFs")
    return page_urls, pdf_urls
