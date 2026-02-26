"""
YCCE-AI Configuration
Loads environment variables and provides centralized access to all settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Supabase ───────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# ── Scraper ────────────────────────────────────────────────────
TARGET_DOMAIN = os.getenv("TARGET_DOMAIN", "https://www.ycce.edu")
MAX_PAGES = int(os.getenv("MAX_PAGES", "500"))
MAX_PDFS = int(os.getenv("MAX_PDFS", "200"))

# ── Chunking ───────────────────────────────────────────────────
CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 100    # overlapping characters between chunks

# ── Database Table ─────────────────────────────────────────────
KNOWLEDGE_TABLE = "ycce_knowledge"

# ── Embedding ──────────────────────────────────────────────────
EMBEDDING_DIMENSIONS = 384  # gte-small model output

# ── Validation ─────────────────────────────────────────────────
def validate():
    """Ensure all critical env vars are set."""
    missing = []
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_SERVICE_KEY:
        missing.append("SUPABASE_SERVICE_KEY")
    if not SUPABASE_ANON_KEY:
        missing.append("SUPABASE_ANON_KEY")
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    print("[OK] Configuration validated successfully.")
