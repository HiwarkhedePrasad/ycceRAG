"""
main.py -- YCCE-AI Pipeline Orchestrator

The entry point that orchestrates the full pipeline:
  1. Crawl the YCCE website (Spider)
  2. Extract text from HTML pages and PDFs (Extractor)
  3. Chunk the extracted text (Chunker)
  4. Compute hashes and detect changes (Deduplicator)
  5. Embed changed chunks using Supabase Edge Function (gte-small)
  6. Upsert into Supabase Vector DB (Storage)

New information ALWAYS takes priority over old information.
"""

import sys
import io
import time

# Fix Windows console encoding for Unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import config
from crawler.spider import crawl
from crawler.extractor import extract_text_from_html
from crawler.pdf_parser import extract_text_from_pdf
from processor.chunker import chunk_document
from processor.deduplicator import compute_hashes_for_chunks, find_changed_urls
from processor.embedder import embed_texts
from database.supabase_client import (
    get_existing_hashes,
    delete_chunks_for_url,
    upsert_chunks,
)


def run_pipeline():
    """Execute the full automated knowledge pipeline."""
    start = time.time()
    print("=" * 60)
    print("YCCE-AI Pipeline -- Starting Automated Knowledge Sync")
    print("=" * 60)

    # -- Step 0: Validate config
    config.validate()

    # -- Step 1: Crawl
    print("\n[PHASE 1] Crawling the YCCE domain...")
    page_urls, pdf_urls = crawl()

    # -- Step 2: Extract
    print("\n[PHASE 2] Extracting content...")
    documents = []

    for url in page_urls:
        doc = extract_text_from_html(url)
        if doc:
            documents.append(doc)

    for url in pdf_urls:
        doc = extract_text_from_pdf(url)
        if doc:
            documents.append(doc)

    print(f"  [OK] Extracted {len(documents)} documents total.")

    if not documents:
        print("[WARN] No documents extracted. Pipeline complete (nothing to do).")
        return

    # -- Step 3: Chunk
    print("\n[PHASE 3] Chunking documents...")
    all_chunks = []
    for doc in documents:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
    print(f"  [OK] Created {len(all_chunks)} chunks from {len(documents)} documents.")

    # -- Step 4: Deduplicate -- New Info Takes Priority
    print("\n[PHASE 4] Detecting changes (new info takes priority)...")
    all_chunks = compute_hashes_for_chunks(all_chunks)

    existing_hashes = get_existing_hashes()
    changed_urls = find_changed_urls(all_chunks, existing_hashes)

    # Filter to only chunks from changed URLs (+ entirely new URLs)
    new_urls = {c["url"] for c in all_chunks} - set(existing_hashes.keys())
    urls_to_process = changed_urls | new_urls

    if not urls_to_process:
        print("  [OK] No changes detected. Database is already up-to-date!")
        return

    print(f"  [NEW] New URLs: {len(new_urls)}")
    print(f"  [UPD] Changed URLs: {len(changed_urls)}")

    chunks_to_upload = [c for c in all_chunks if c["url"] in urls_to_process]
    print(f"  [TOTAL] Chunks to process: {len(chunks_to_upload)}")

    # -- Step 5: Delete old data for changed URLs
    print("\n[CLEANUP] Purging outdated data for changed URLs...")
    for url in changed_urls:
        delete_chunks_for_url(url)

    # -- Step 6: Embed via Supabase Edge Function (gte-small, 384 dims)
    print(f"\n[PHASE 5] Embedding {len(chunks_to_upload)} chunks via Supabase Edge Function (gte-small)...")
    texts = [c["content"] for c in chunks_to_upload]

    all_embeddings = []
    for i, text in enumerate(texts):
        emb = embed_texts([text])
        all_embeddings.extend(emb)
        if (i + 1) % 10 == 0 or i == len(texts) - 1:
            print(f"  [EMBED] {i + 1}/{len(texts)} chunks done")

    # -- Step 7: Upsert to Supabase
    print("\n[PHASE 6] Uploading to Supabase Vector DB...")

    # Group chunks by URL for organized uploads
    from itertools import groupby
    chunks_with_emb = list(zip(chunks_to_upload, all_embeddings))
    chunks_with_emb.sort(key=lambda x: x[0]["url"])

    for url, group in groupby(chunks_with_emb, key=lambda x: x[0]["url"]):
        group_list = list(group)
        grp_chunks = [g[0] for g in group_list]
        grp_embs = [g[1] for g in group_list]
        upsert_chunks(grp_chunks, grp_embs)

    # -- Done
    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print(f"YCCE-AI Pipeline Complete! ({elapsed:.1f}s)")
    print(f"   Documents processed: {len(documents)}")
    print(f"   Chunks uploaded: {len(chunks_to_upload)}")
    print(f"   New URLs: {len(new_urls)}")
    print(f"   Updated URLs: {len(changed_urls)}")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
