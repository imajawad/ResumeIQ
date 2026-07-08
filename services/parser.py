"""
services/parser.py
==================
Document text extraction service.

Implements the **Strategy Pattern**: all three format-specific extractors
(PDF, DOCX, OCR image) share the same ``extract_text(file, extension)``
public interface. Flask routes select the strategy based on file extension;
no format logic leaks into routing code.

Supported formats:
    pdf  — PyMuPDF (fitz) for text-layer PDFs
    docx — python-docx for Word documents
    png/jpg/jpeg — Tesseract OCR via pytesseract for scanned images
"""

import io
from typing import BinaryIO


# ---------------------------------------------------------------------------
# Private strategies
# ---------------------------------------------------------------------------

def _extract_pdf(file_stream: BinaryIO) -> str:
    """Extract text from a PDF file using pypdf.

    Iterates over every page and concatenates extracted text blocks.
    Falls back gracefully if a page yields no text (e.g., image-only pages).

    Args:
        file_stream: Readable binary stream of the PDF file.

    Returns:
        str: Concatenated text from all pages.

    Raises:
        ValueError: If pypdf cannot open the stream as a valid PDF.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pypdf is not installed. Run: pip install pypdf")

    try:
        raw_bytes = file_stream.read()
        reader = PdfReader(io.BytesIO(raw_bytes))
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
        return "\n".join(pages_text)
    except Exception as exc:
        raise ValueError(f"Failed to parse PDF: {exc}") from exc


def _extract_docx(file_stream: BinaryIO) -> str:
    """Extract text from a DOCX file using python-docx.

    Reads all paragraph objects and joins their text, preserving line breaks.

    Args:
        file_stream: Readable binary stream of the DOCX file.

    Returns:
        str: All paragraph text joined with newlines.

    Raises:
        ValueError: If python-docx cannot parse the stream.
    """
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is not installed. Run: pip install python-docx")

    try:
        doc = Document(io.BytesIO(file_stream.read()))
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)
    except Exception as exc:
        raise ValueError(f"Failed to parse DOCX: {exc}") from exc


def _extract_image(file_stream: BinaryIO) -> str:
    """Extract text from a scanned image resume using Tesseract OCR.

    Uses pytesseract with default language (English). Converts the byte
    stream to a PIL Image before passing to Tesseract.

    Args:
        file_stream: Readable binary stream of a PNG, JPG, or JPEG image.

    Returns:
        str: OCR-extracted text.

    Raises:
        ValueError: If OCR fails or the image cannot be opened.
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise ImportError(
            "pytesseract and Pillow are required for OCR. "
            "Run: pip install pytesseract Pillow"
        )

    try:
        image = Image.open(io.BytesIO(file_stream.read()))
        # Use page segmentation mode 6: treat image as a uniform block of text
        text = pytesseract.image_to_string(image, config="--psm 6")
        return text
    except Exception as exc:
        raise ValueError(f"OCR failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Public interface (Strategy dispatcher)
# ---------------------------------------------------------------------------

_STRATEGY_MAP = {
    "pdf": _extract_pdf,
    "docx": _extract_docx,
    "png": _extract_image,
    "jpg": _extract_image,
    "jpeg": _extract_image,
}


def extract_text(file, extension: str) -> str:
    """Dispatch file parsing to the correct strategy based on extension.

    This is the single public interface for the parser module. Callers
    (Flask routes, tests) never need to know which concrete extractor runs.

    Args:
        file: A werkzeug FileStorage object or any readable binary stream.
        extension: Lowercase file extension without the leading dot
                   (e.g. ``"pdf"``, ``"docx"``, ``"png"``).

    Returns:
        str: Extracted text content.

    Raises:
        ValueError: If the extension is unsupported or parsing fails.
    """
    ext = extension.lower().strip(".")
    strategy = _STRATEGY_MAP.get(ext)
    if strategy is None:
        supported = ", ".join(_STRATEGY_MAP.keys())
        raise ValueError(
            f"Unsupported file extension '{ext}'. Supported: {supported}"
        )

    # Rewind the stream in case it has been partially read upstream
    if hasattr(file, "seek"):
        file.seek(0)

    return strategy(file)
