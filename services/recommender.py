"""
services/recommender.py
========================
Learning resource recommendation service using Grok API.

Dynamically maps identified skill gaps to highly relevant courses
by querying the LLM for recommendations.
"""

import json
from typing import List, Dict, Any
from services.grok_client import get_grok_client

def get_recommendations(missing_skills: List[str]) -> List[Dict[str, Any]]:
    """Return exactly 4-5 learning resource recommendations for the missing skills.

    Args:
        missing_skills: List of skill strings identified as gaps.

    Returns:
        List[dict]: Recommendations, each with keys ``skill``, ``title``, 
                    ``platform``, ``level``.
    """
    if not missing_skills:
        return []

    client = get_grok_client()
    
    prompt = (
        "You are an expert career coach. The candidate is missing the following skills "
        f"for a target job: {json.dumps(missing_skills)}.\n\n"
        "Recommend exactly 4 to 5 high-quality learning courses or resources that will help "
        "the candidate learn these missing skills.\n\n"
        "Return ONLY a JSON array of objects with the exact structure below. "
        "Do not include markdown blocks or any other text.\n"
        "[\n"
        "  {\n"
        "    \"skill\": \"The missing skill addressed\",\n"
        "    \"title\": \"Title of the course\",\n"
        "    \"platform\": \"Platform (e.g., Coursera, YouTube, Udemy)\",\n"
        "    \"level\": \"Beginner, Intermediate, or Advanced\"\n"
        "  }\n"
        "]"
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that strictly outputs JSON arrays of objects."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        content = response.choices[0].message.content.strip()
        
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        content = content.strip()
        
        recommendations = json.loads(content)
        
        # Ensure we return 4-5 items if possible
        if isinstance(recommendations, list):
            # Set a placeholder URL since Grok doesn't always know exact URLs reliably,
            # or the frontend can just render the title and platform.
            # In the original, url was a key. We'll add a dummy search URL if needed,
            # or we can ask Grok for URLs, but hallucinations are common. 
            # Let's construct a search URL.
            for rec in recommendations:
                if "url" not in rec:
                    query = f"{rec.get('title', '')} {rec.get('platform', '')}".replace(" ", "+")
                    rec["url"] = f"https://www.google.com/search?q={query}"
            return recommendations[:5]
        else:
            return []
            
    except Exception as e:
        print(f"Error calling Grok for recommendations: {e}")
        return []
