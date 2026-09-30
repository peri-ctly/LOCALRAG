

"""
Creates sentence-aware chunks from PDF pages.
A chunk never crosses a page boundary.
"""

import re

CHUNK_SIZE = 900
MIN_CHUNK_SIZE = 150


def split_sentences(text):
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def create_chunks(pages):
    chunks = []
    chunk_index = 0

    for page in pages:
        page_number = page["page_number"]
        sentences = split_sentences(page["text"])
        if not sentences:
            continue

        current_chunk = ""

        for sentence in sentences:
            candidate = f"{current_chunk} {sentence}".strip()

            if len(candidate) <= CHUNK_SIZE:
                current_chunk = candidate
                continue

            chunks.append({"chunk_index": chunk_index, "page_number": page_number, "text": current_chunk})
            chunk_index += 1
            current_chunk = sentence

        if not current_chunk:
            continue

        if len(current_chunk) < MIN_CHUNK_SIZE and chunks and chunks[-1]["page_number"] == page_number:
            chunks[-1]["text"] += " " + current_chunk
        else:
            chunks.append({"chunk_index": chunk_index, "page_number": page_number, "text": current_chunk})
            chunk_index += 1

    return chunks
