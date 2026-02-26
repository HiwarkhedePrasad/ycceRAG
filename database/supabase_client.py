"""
supabase_client.py — Manages all interactions with the Supabase Vector Database.

Responsibilities:
 • Connect to Supabase using the service role key.
 • Fetch existing content hashes per URL for deduplication.
 • Delete old chunks for a URL when content has changed.
 • Upsert new chunks with their embeddings.
"""

from datetime import datetime, timezone
from supabase import create_client, Client
import config


_client: Client | None = None


def get_client() -> Client:
    """Lazy singleton for the Supabase client."""
    global _client
    if _client is None:
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
    return _client


def get_existing_hashes() -> dict[str, set[str]]:
    """
    Fetches all (url, content_hash) pairs from the knowledge table.
    Returns a dict: url -> set of content_hashes.
    """
    client = get_client()
    table = config.KNOWLEDGE_TABLE

    result = client.table(table).select("url, content_hash").execute()
    hashes: dict[str, set[str]] = {}
    for row in result.data:
        url = row["url"]
        hashes.setdefault(url, set()).add(row["content_hash"])
    return hashes


def delete_chunks_for_url(url: str):
    """Delete ALL existing chunks for a given URL (to be replaced by fresh data)."""
    client = get_client()
    client.table(config.KNOWLEDGE_TABLE).delete().eq("url", url).execute()
    print(f"  🗑️  Deleted old chunks for: {url}")


def upsert_chunks(chunks: list[dict], embeddings: list[list[float]]):
    """
    Insert new chunks with their embeddings into the knowledge table.
    Each chunk dict must have: url, title, type, chunk_index, content, content_hash.
    """
    client = get_client()
    table = config.KNOWLEDGE_TABLE
    now = datetime.now(timezone.utc).isoformat()

    rows = []
    for chunk, embedding in zip(chunks, embeddings):
        rows.append({
            "url": chunk["url"],
            "chunk_index": chunk["chunk_index"],
            "content": chunk["content"],
            "content_hash": chunk["content_hash"],
            "embedding": embedding,
            "metadata": {
                "title": chunk["title"],
                "type": chunk["type"],
                "updated_at": now,
            },
        })

    # Batch insert (Supabase supports bulk inserts)
    BATCH_SIZE = 100
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        client.table(table).insert(batch).execute()
        print(f"  💾 Inserted batch {i // BATCH_SIZE + 1} ({len(batch)} rows)")

    print(f"  ✅ Upserted {len(rows)} chunks for: {chunks[0]['url'] if chunks else 'N/A'}")
