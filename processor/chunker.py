"""
chunker.py — Splits extracted text into digestible chunks.

Uses LangChain's RecursiveCharacterTextSplitter for intelligent
splitting that respects sentence and paragraph boundaries.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
import config


def chunk_document(document: dict) -> list[dict]:
    """
    Takes a document dict (with 'url', 'title', 'content', 'type')
    and returns a list of chunk dicts, each containing:
      - url, title, type: inherited from the parent document
      - chunk_index: position of the chunk
      - content: the chunk text
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    texts = splitter.split_text(document["content"])

    chunks = []
    for i, text in enumerate(texts):
        chunks.append({
            "url": document["url"],
            "title": document["title"],
            "type": document["type"],
            "chunk_index": i,
            "content": text,
        })

    return chunks
