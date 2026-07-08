"""
services/matcher.py
====================
Semantic skill matching service using Grok API.

Compares resume skills against job description skills to find matches,
missing requirements, and an overall match score based on AI reasoning.
"""

import json
from typing import Dict, List, Any
from services.grok_client import get_grok_client

def compute_match(
    resume_skills: List[str],
    jd_skills: List[str],
) -> Dict[str, Any]:
    """Compute semantic skill match between resume and job description using Grok.

    Args:
        resume_skills: List of skill strings extracted from the resume.
        jd_skills:     List of skill strings extracted from the job description.

    Returns:
        dict with keys:
            ``score``          (int)       — 0–100 match percentage
            ``matched_skills`` (List[str]) — JD skills found in resume
            ``missing_skills`` (List[str]) — JD skills not found in resume
    """
    if not jd_skills:
        return {
            "score": 0,
            "matched_skills": [],
            "missing_skills": [],
        }

    if not resume_skills:
        return {
            "score": 0,
            "matched_skills": [],
            "missing_skills": list(jd_skills),
        }

    client = get_grok_client()
    
    prompt = (
        "You are an expert technical recruiter analyzing a candidate's fit for a job. "
        "I will provide a list of skills the candidate possesses (Resume Skills) "
        "and a list of skills required for the job (Job Description Skills).\n\n"
        "Your task is to determine which Job Description skills the candidate has "
        "(these are 'matched_skills') and which ones they lack ('missing_skills'). "
        "Account for semantic similarities (e.g., 'Node' matches 'Node.js', "
        "'Machine Learning' matches 'ML').\n\n"
        "Finally, calculate a match score out of 100 based on the proportion of critical "
        "skills met.\n\n"
        f"Resume Skills: {json.dumps(resume_skills)}\n"
        f"Job Description Skills: {json.dumps(jd_skills)}\n\n"
        "Return ONLY a JSON object with this exact structure:\n"
        "{\n"
        "  \"score\": <integer 0-100>,\n"
        "  \"matched_skills\": [\"list\", \"of\", \"strings\"],\n"
        "  \"missing_skills\": [\"list\", \"of\", \"strings\"]\n"
        "}\n"
        "Do not include markdown blocks, explanations, or any other text."
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that strictly outputs JSON objects."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        content = content.strip()
        
        result = json.loads(content)
        
        return {
            "score": result.get("score", 0),
            "matched_skills": result.get("matched_skills", []),
            "missing_skills": result.get("missing_skills", jd_skills) # fallback
        }
            
    except Exception as e:
        print(f"Error calling Grok for matching: {e}")
        # Fallback to basic sets if API fails
        r_set = {s.lower() for s in resume_skills}
        matched = [s for s in jd_skills if s.lower() in r_set]
        missing = [s for s in jd_skills if s.lower() not in r_set]
        score = int((len(matched) / len(jd_skills)) * 100) if jd_skills else 0
        return {
            "score": score,
            "matched_skills": matched,
            "missing_skills": missing
        }
