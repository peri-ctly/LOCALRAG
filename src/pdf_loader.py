
"""
Reads text from PDF files using pypdf.
"""

from pypdf import PdfReader


def load_pdf_pages(file_path):
    reader = PdfReader(file_path)
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()

        if page_text:
            pages.append({"page_number": page_number, "text": page_text})

    return pages


def load_pdf(file_path):
    """Kept for backward compatibility."""
    pages = load_pdf_pages(file_path)
    return "\n".join(page["text"] for page in pages)
    