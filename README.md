# ⚡ ResumeIQ — AI-Powered Resume Analyzer

## 🌐 Live Application

**→ [https://resumeiq-6ryu.onrender.com](https://resumeiq-6ryu.onrender.com)**

---

## 🚀 What ResumeIQ Does

ResumeIQ analyzes your resume against a job description using AI-powered semantic matching — not just keyword comparison. It tells you:

- **Match Score (0–100%)** — how well your resume fits the role
- **Matched Skills** — what you already have
- **Missing Skills** — what gaps to address
- **ATS Compatibility** — whether your resume will pass Applicant Tracking Systems
- **Learning Resources** — free Coursera / YouTube courses for each skill gap
- **PDF Evaluation Report** — download a beautifully formatted graphical PDF of your analysis

---

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10 + Flask |
| AI / NLP | Groq API (Llama 3.3 70B) |
| OCR | Tesseract + pytesseract |
| File Parsing | PyMuPDF (PDF) · python-docx (DOCX) |
| ATS Analysis | pdfplumber |
| PDF Generation | fpdf2 + matplotlib |
| Frontend | HTML5 · CSS3 · Vanilla JavaScript |
| Charts | Chart.js 4 |
| CI/CD | GitHub Actions |
| Deployment | Render (free tier · gunicorn) |

---

## 🗂️ Repository Structure

```
resumeiq/
├── app.py                      # Flask entry point + routes
├── services/
│   ├── parser.py               # PDF / DOCX / OCR text extraction
│   ├── skill_extractor.py      # NLP skill identification (Groq/Llama3)
│   ├── matcher.py              # Semantic matching (Groq/Llama3)
│   ├── ats_checker.py          # ATS compatibility analysis
│   ├── pdf_generator.py        # PDF Evaluation report generation
│   └── recommender.py          # Course recommendations per skill gap
├── static/
│   ├── css/style.css           # Application styles
│   └── js/main.js              # Frontend logic + Chart.js rendering
├── templates/
│   └── index.html              # Single-page HTML interface
├── tests/
│   ├── test_parser.py
│   ├── test_extractor.py
│   ├── test_matcher.py
│   ├── test_gap_analysis.py
│   └── test_ats_checker.py
├── .env.example                # Environment variables template
├── .github/workflows/ci.yml    # GitHub Actions CI/CD
├── requirements.txt
├── Procfile
├── DESIGN_AND_TESTING.md
└── README.md
```

---

## ⚙️ Local Setup

### Prerequisites

- Python 3.10+
- Tesseract OCR installed on your system
- A free Groq API Key

#### Install Tesseract

```bash
# macOS
brew install tesseract

# Ubuntu / Debian
sudo apt-get install tesseract-ocr

# Windows — download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki
```

### Install & Run

```bash
# Clone the repository
git clone https://github.com/imajawad/ResumeIQ.git
cd ResumeIQ

# Create virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure Environment Variables
# Create a .env file in the root directory and add:
GROQ_API_KEY="your_groq_api_key_here"

# Run the application
python app.py
```

Open your browser at **http://localhost:5000**

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=services --cov-report=term-missing
```

---

## 🚢 Deployment (Render)

1. Push this repository to GitHub
2. Create a new **Web Service** on [render.com](https://render.com)
3. Connect your GitHub repository
4. Set:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: Python 3.10
5. Add an Environment Variable for `GROQ_API_KEY`.
6. Click **Deploy**

> **Note**: Render free tier may have cold-start delays (~30 seconds on first request). The `/health` endpoint is available for uptime monitoring.

---

## 📄 Documentation

See **[DESIGN_AND_TESTING.md](DESIGN_AND_TESTING.md)** for full architecture decisions, design patterns, deployment rationale, and testing strategy.
