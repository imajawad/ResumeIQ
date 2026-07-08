"""
ResumeIQ — AI-Powered Resume Analyzer
======================================
Flask application entry point.
Defines all API routes and wires together the service layer.

Routes:
    GET  /           — Serve the single-page HTML interface
    POST /analyze    — Core analysis endpoint (file + JD → JSON results)
    GET  /health     — Health check for Render uptime monitoring
"""

import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename

# Load environment variables from .env file for local development
load_dotenv()

from services.parser import extract_text
from services.skill_extractor import extract_skills
from services.matcher import compute_match
from services.ats_checker import check_ats
from services.recommender import get_recommendations
from services.pdf_generator import generate_evaluation_pdf

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload limit

ALLOWED_EXTENSIONS = {"pdf", "docx", "png", "jpg", "jpeg"}


def allowed_file(filename: str) -> bool:
    """Return True if the file extension is in the allowed set.

    Args:
        filename: Original filename from the upload.

    Returns:
        bool: True if extension is supported, False otherwise.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Serve the single-page ResumeIQ interface."""
    return render_template("index.html")


@app.route("/health")
def health():
    """Health-check endpoint used by Render to confirm the app is alive.

    Returns:
        JSON: {"status": "ok"}
    """
    return jsonify({"status": "ok"}), 200


@app.route("/analyze", methods=["POST"])
def analyze():
    """Core analysis endpoint.

    Expects a multipart/form-data POST with:
        - ``resume``        : file (PDF, DOCX, PNG, JPG/JPEG)
        - ``job_description``: text (plain-text job description)

    Returns:
        JSON (200): Full analysis result including match score, matched/missing
                    skills, gap recommendations, ATS flags, and course links.
        JSON (400): Validation error details.
        JSON (500): Internal server error details.
    """
    # ---- input validation --------------------------------------------------
    if "resume" not in request.files:
        return jsonify({"error": "No resume file provided."}), 400

    resume_file = request.files["resume"]
    job_description = request.form.get("job_description", "").strip()

    if resume_file.filename == "":
        return jsonify({"error": "Resume file has no name."}), 400

    if not allowed_file(resume_file.filename):
        return jsonify({
            "error": f"Unsupported file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 400

    if not job_description:
        return jsonify({"error": "Job description is required."}), 400

    if len(job_description) < 50:
        return jsonify({"error": "Job description is too short (minimum 50 characters)."}), 400

    # ---- processing --------------------------------------------------------
    try:
        filename = secure_filename(resume_file.filename)
        extension = filename.rsplit(".", 1)[1].lower()

        # 1. Parse resume text
        resume_text = extract_text(resume_file, extension)
        if not resume_text or len(resume_text.strip()) < 30:
            return jsonify({"error": "Could not extract readable text from the resume."}), 400

        # 2. Extract skills from both documents
        resume_skills = extract_skills(resume_text)
        jd_skills = extract_skills(job_description)

        if not jd_skills:
            return jsonify({
                "error": "No recognizable skills found in the job description. "
                         "Please ensure it lists specific technical or professional skills."
            }), 400

        # 3. Semantic matching + scoring
        match_result = compute_match(resume_skills, jd_skills)

        # 4. ATS compatibility check (PDF only)
        ats_result = check_ats(resume_file, extension)

        # 5. Course recommendations for missing skills
        recommendations = get_recommendations(match_result["missing_skills"])

        # ---- response -------------------------------------------------------
        return jsonify({
            "match_score": match_result["score"],
            "matched_skills": match_result["matched_skills"],
            "missing_skills": match_result["missing_skills"],
            "resume_skills": resume_skills,
            "jd_skills": jd_skills,
            "recommendations": recommendations,
            "ats": ats_result,
        }), 200

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # pylint: disable=broad-except
        app.logger.error("Unexpected error in /analyze: %s", exc, exc_info=True)
        return jsonify({"error": f"Internal Server Error: {str(exc)}"}), 500


@app.route("/download-report", methods=["POST"])
def download_report():
    """Generates and returns a PDF report based on analysis results."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        pdf_path = generate_evaluation_pdf(data)
        return send_file(
            pdf_path, 
            as_attachment=True, 
            download_name="ResumeIQ_Evaluation_Report.pdf", 
            mimetype="application/pdf"
        )
    except Exception as exc:
        app.logger.error("Unexpected error in /download-report: %s", exc, exc_info=True)
        return jsonify({"error": f"Internal Server Error: {str(exc)}"}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
