"""
pdf_parser.py — Downloads PDFs and extracts text page-by-page.

Uses PyMuPDF (fitz) for robust text extraction, including
table-heavy academic documents like syllabi and calendars.
"""

import os
import tempfile
import requests
import fitz  # PyMuPDF


def extract_text_from_pdf(url: str) -> dict | None:
    """
    Downloads a PDF from `url`, extracts all text page-by-page,
    and returns a dict with:
      - url: source URL
      - title: derived from filename
      - content: full extracted text
      - type: "pdf"
    Returns None if the extraction fails.
    """
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
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
            text = page.get_text("text")
            if text.strip():
                pages_text.append(f"--- Page {page_num + 1} ---\n{text.strip()}")

        doc.close()
    except Exception as e:
        print(f"  ❌ PDF parsing failed for {url}: {e}")
        return None
    finally:
        os.unlink(tmp_path)

    full_text = "\n\n".join(pages_text)
    if not full_text.strip():
        print(f"  ⚠️  PDF had no extractable text: {url}")
        return None

    # Derive title from the PDF filename
    filename = url.split("/")[-1].split("?")[0]
    title = filename.replace(".pdf", "").replace("_", " ").replace("-", " ").title()

    return {
        "url": url,
        "title": title,
        "content": full_text,
        "type": "pdf",
    }
