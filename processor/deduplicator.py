"""
deduplicator.py — Tracks content changes and ensures new info takes priority.

Creates SHA-256 hashes of chunk content to detect changes.
When a URL is re-scraped and its content has changed, all OLD chunks
for that URL are purged and replaced with the NEW chunks, guaranteeing
that new information always takes absolute priority.
"""

import hashlib


def compute_hash(text: str) -> str:
    """Generate a SHA-256 hash for a text string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_hashes_for_chunks(chunks: list[dict]) -> list[dict]:
    """
    Adds a 'content_hash' field to each chunk dict.
    Returns the updated list.
    """
    for chunk in chunks:
        chunk["content_hash"] = compute_hash(chunk["content"])
    return chunks


def find_changed_urls(new_chunks: list[dict], existing_hashes: dict[str, set[str]]) -> set[str]:
    """
    Compares new chunk hashes against existing hashes per URL.
    Returns the set of URLs whose content has changed (i.e., needs re-upload).

    Args:
        new_chunks: list of chunk dicts with 'url' and 'content_hash'
        existing_hashes: dict mapping url -> set of content_hashes already in DB
    """
    changed_urls = set()

    # Group new chunks by URL
    new_by_url: dict[str, set[str]] = {}
    for chunk in new_chunks:
        url = chunk["url"]
        new_by_url.setdefault(url, set()).add(chunk["content_hash"])

    for url, new_hash_set in new_by_url.items():
        old_hash_set = existing_hashes.get(url, set())
        if new_hash_set != old_hash_set:
            changed_urls.add(url)

    return changed_urls
