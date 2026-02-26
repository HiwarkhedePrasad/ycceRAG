"""
embedder.py — Generates embeddings via the Supabase Edge Function.

Uses the built-in gte-small model running inside Supabase Edge Runtime.
No external API key needed — zero rate limits!
"""

import time
import requests
import config


def _call_embed(text: str, retries: int = 3) -> list[float]:
    """Call the Edge Function for a single text with retries."""
    url = f"{config.SUPABASE_URL}/functions/v1/embed"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.SUPABASE_ANON_KEY}",
    }
    payload = {"input": text}

    for attempt in range(retries):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            if resp.status_code == 546 or resp.status_code >= 500:
                wait = 2 ** attempt * 2
                print(f"    [RETRY] Edge Function returned {resp.status_code}, waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()["embedding"]
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                wait = 2 ** attempt * 2
                print(f"    [RETRY] Request error: {e}, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Failed to embed after {retries} retries")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts one at a time via the Edge Function.
    Returns list of 384-dimensional vectors.
    """
    embeddings = []
    for text in texts:
        emb = _call_embed(text)
        embeddings.append(emb)
    return embeddings


def embed_single(text: str) -> list[float]:
    """Embed a single text string (e.g., a user query)."""
    return _call_embed(text)
