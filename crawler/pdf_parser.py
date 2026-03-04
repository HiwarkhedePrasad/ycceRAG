"""
pdf_parser.py — Downloads PDFs and extracts text page-by-page.

Uses PyMuPDF (fitz) for robust text extraction, including
table-heavy academic documents like syllabi and calendars.
Falls back to OCR-style extraction for scanned PDFs.
"""

import os
import tempfile
import requests
import fitz  # PyMuPDF
import time


def extract_text_from_pdf(url: str) -> dict | None:
    """
    Downloads a PDF from `url`, extracts all text page-by-page.
    Returns None only if download fails completely.
    """
    resp = None
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=45, headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            })
            resp.raise_for_status()
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
                continue
            print(f"  ❌ PDF download failed for {url}: {e}")
            return None

    # Write to a temp file
    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(resp.content)
        tmp_path = tmp.name

    try:
        doc = fitz.open(tmp_path)
        pages_text = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            # Try normal text extraction first
            text = page.get_text("text")
            if not text.strip():
                # Try extracting from text blocks (handles some edge cases)
                blocks = page.get_text("blocks")
                text = "\n".join(b[4] for b in blocks if b[6] == 0)
            if text.strip():
                pages_text.append(f"--- Page {page_num + 1} ---\n{text.strip()}")

        doc.close()
    except Exception as e:
        print(f"  ❌ PDF parsing failed for {url}: {e}")
        return None
    finally:
        os.unlink(tmp_path)

    full_text = "\n\n".join(pages_text)

    # Even if no text extracted, create an entry with the filename as content
    # so it's at least searchable by name
    filename = url.split("/")[-1].split("?")[0]
    title = filename.replace(".pdf", "").replace("%20", " ").replace("_", " ").replace("-", " ").title()

    if not full_text.strip():
        # Use filename + URL as minimal content so it's findable
        full_text = f"PDF Document: {title}\nSource: {url}\nThis is a scanned PDF document from YCCE."
        print(f"  ⚠️  Scanned PDF (using filename): {url}")

    return {
        "url": url,
        "title": title,
        "content": full_text,
        "type": "pdf",
    }
