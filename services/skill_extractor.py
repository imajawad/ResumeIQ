"""
services/skill_extractor.py
============================
AI-based skill identification service using Grok API.

Extracts all professional and technical skills from free-form text
by leveraging a Large Language Model for semantic understanding.
"""

import json
from typing import List
from services.grok_client import get_grok_client

def extract_skills(text: str) -> List[str]:
    """Identify and return a deduplicated list of skills from free-form text using Grok.

    Args:
        text: Raw text extracted from a resume or job description.

    Returns:
        List[str]: Sorted, deduplicated list of identified skill strings.
    """
    if not text or not text.strip():
        return []

    client = get_grok_client()
    
    prompt = (
        "You are an expert technical recruiter and resume analyzer. "
        "Extract a comprehensive list of all technical and professional skills "
        "explicitly mentioned in the following text. Do NOT infer implicit soft skills "
        "(like 'communication', 'problem solving', or 'adaptability') unless they are explicitly written. "
        "Return ONLY a JSON array of strings (e.g., [\"Python\", \"Machine Learning\"]). "
        "Do not include markdown blocks, explanations, or any other text.\n\n"
        f"Text:\n{text}"
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that strictly outputs JSON arrays of strings."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        
        # Remove markdown JSON blocks if the model included them despite instructions
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        content = content.strip()
        
        skills = json.loads(content)
        
        if isinstance(skills, list):
            # Clean, lower, deduplicate, and sort
            unique_skills = set(str(s).strip() for s in skills if str(s).strip())
            return sorted(list(unique_skills), key=str.lower)
        else:
            return []
            
    except Exception as e:
        # Log the error in a real app, but here we can just return empty or propagate
        print(f"Error calling Grok for skill extraction: {e}")
        return []
