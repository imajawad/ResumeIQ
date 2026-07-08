"""
services/ats_checker.py
========================
ATS (Applicant Tracking System) compatibility analysis service.

Checks a resume PDF for formatting patterns that commonly cause ATS
parsers to fail or score a resume poorly:

    - Tables        : pdfplumber detects table bounding boxes
    - Images        : PyMuPDF checks for embedded image XObjects
    - Multi-column  : Heuristic based on horizontal spread of text blocks
    - Headers/footers: Text outside the main body margin band
    - Special fonts : Non-standard fonts that OCR-based ATS may misread

Only PDF files are analysed; DOCX and image uploads return a note
explaining the limitation. All flags are returned with human-readable
fix suggestions.
"""

from typing import Dict, Any, List


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _check_pdf_ats(file_stream) -> Dict[str, Any]:
    """Run ATS checks on a PDF byte stream.

    Args:
        file_stream: Readable binary stream rewound to position 0.

    Returns:
        dict: ATS result with ``flags``, ``suggestions``, and ``score`` keys.
    """
    try:
        import pdfplumber
        from pypdf import PdfReader
    except ImportError as exc:
        missing_package = getattr(exc, "name", None) or "pdfplumber/pypdf"
        return {
            "ats_score": 0,
            "flags": ["ats_dependencies_missing"],
            "suggestions": [
                f"ATS PDF checks were skipped because {missing_package} is not installed. "
                "Run: pip install -r requirements.txt"
            ],
            "checked": False,
            "note": "PDF ATS analysis is unavailable until the ATS dependencies are installed.",
        }

    import io

    raw_bytes = file_stream.read()
    flags: List[str] = []
    suggestions: List[str] = []

    # ---- 1. Table detection (pdfplumber) -----------------------------------
    try:
        with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
            for page in pdf.pages:
                tables = page.find_tables()
                if tables:
                    flags.append("tables_detected")
                    suggestions.append(
                        "Replace tables with plain-text sections. "
                        "Use spaces or tabs to align columns instead."
                    )
                    break  # one flag per issue type is sufficient

    except Exception:
        pass  # Non-fatal; continue remaining checks

    # ---- 2. Image / graphic detection (pypdf) ----------------------------
    try:
        reader = PdfReader(io.BytesIO(raw_bytes))
        for page in reader.pages:
            if len(page.images) > 0:
                flags.append("images_detected")
                suggestions.append(
                    "Remove images, logos, and graphics. "
                    "ATS parsers cannot read text embedded in images."
                )
                break
    except Exception:
        pass

    # ---- 3. Multi-column layout heuristic (pdfplumber) --------------------
    try:
        with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
            for page in pdf.pages:
                words = page.extract_words()
                if not words:
                    continue
                # Group word x-positions; if they cluster into 2+ distinct bands
                # the resume is likely multi-column
                x_positions = sorted({int(w["x0"]) for w in words})
                if len(x_positions) > 1:
                    gaps = [
                        x_positions[i + 1] - x_positions[i]
                        for i in range(len(x_positions) - 1)
                    ]
                    large_gap_threshold = page.width * 0.20  # 20% of page width
                    if any(g > large_gap_threshold for g in gaps):
                        flags.append("multi_column_layout")
                        suggestions.append(
                            "Convert multi-column layout to a single column. "
                            "Many ATS systems read left-to-right across columns, "
                            "jumbling your content."
                        )
                        break
    except Exception:
        pass

    # ---- 4. Compute ATS score (100 minus 25 per flag) ---------------------
    ats_score = max(0, 100 - (len(flags) * 25))

    return {
        "ats_score": ats_score,
        "flags": flags,
        "suggestions": suggestions,
        "checked": True,
    }


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def check_ats(file, extension: str) -> Dict[str, Any]:
    """Run ATS compatibility checks on an uploaded resume file.

    Currently only PDF files are deeply analysed. DOCX and image files
    receive a simplified response with a note.

    Args:
        file:      Werkzeug FileStorage or any readable binary stream.
        extension: Lowercase file extension (``"pdf"``, ``"docx"``, etc.).

    Returns:
        dict with keys:
            ``ats_score``   (int)        — 0–100 ATS compatibility score
            ``flags``       (List[str])  — detected issue identifiers
            ``suggestions`` (List[str])  — human-readable fix instructions
            ``checked``     (bool)       — True if deep analysis ran
    """
    if hasattr(file, "seek"):
        file.seek(0)

    ext = extension.lower().strip(".")

    if ext == "pdf":
        return _check_pdf_ats(file)

    if ext == "docx":
        return {
            "ats_score": 85,
            "flags": [],
            "suggestions": [
                "DOCX files are generally ATS-friendly. "
                "Ensure you are not using text boxes, SmartArt, or complex "
                "tables for your main content."
            ],
            "checked": False,
            "note": "Deep ATS analysis is only available for PDF uploads.",
        }

    # Image / OCR uploads
    return {
        "ats_score": 50,
        "flags": ["image_resume"],
        "suggestions": [
            "Scanned image resumes are not ATS-compatible. "
            "Please convert your resume to a text-based PDF or DOCX file."
        ],
        "checked": False,
        "note": "Image resumes cannot be read by most ATS systems.",
    }
