import io

from docx import Document
from fastapi import HTTPException
from pypdf import PdfReader


def extract_text(filename: str, content: bytes) -> str:
    """
    Extract plain text from an uploaded resume file.
    Supports .pdf, .docx, and .txt. Raises HTTPException(400) for anything
    else or for files we can't get text out of.
    """
    lower = filename.lower()

    if lower.endswith(".pdf"):
        text = _extract_pdf(content)
    elif lower.endswith(".docx"):
        text = _extract_docx(content)
    elif lower.endswith(".txt"):
        text = content.decode("utf-8", errors="ignore")
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type for '{filename}'. Upload a .pdf, .docx, or .txt file.",
        )

    text = text.strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail=f"Couldn't extract any text from '{filename}'. "
            "If it's a scanned/image PDF, try exporting a text-based version.",
        )
    return text


def _extract_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs)
