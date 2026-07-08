import os
import sys
import json
from pathlib import Path

# Add the project root to the python path so we can import services
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from services.skill_extractor import extract_skills
from services.matcher import compute_match
from dotenv import load_dotenv

load_dotenv()

def evaluate():
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY environment variable is not set.")
        print("Cannot run LLM evaluation without an API key.")
        return

    ground_truth_path = os.path.join(os.path.dirname(__file__), "ground_truth.json")
    
    with open(ground_truth_path, 'r') as f:
        cases = json.load(f)

    total_tp = 0
    total_fp = 0
    total_fn = 0

    print("=========================================")
    print("ResumeIQ AI Performance Evaluation")
    print("=========================================\n")

    for idx, case in enumerate(cases, 1):
        print(f"Running Case {idx}: {case['id']}...")
        
        # 1. Extract skills from Resume and JD
        resume_skills = extract_skills(case["resume_text"])
        jd_skills = extract_skills(case["jd_text"])
        
        # 2. Compute matches
        match_results = compute_match(resume_skills, jd_skills)
        predicted_matches = set(s.lower() for s in match_results["matched_skills"])
        
        expected_matches = set(s.lower() for s in case["expected_matches"])

        # Calculate TP, FP, FN for this case
        # True Positives: Skills in both predicted and expected
        tp = len(predicted_matches.intersection(expected_matches))
        # False Positives: Skills predicted but not expected
        fp = len(predicted_matches - expected_matches)
        # False Negatives: Skills expected but not predicted
        fn = len(expected_matches - predicted_matches)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        print(f"  Predicted Matches: {sorted(list(predicted_matches))}")
        print(f"  Expected Matches : {sorted(list(expected_matches))}")
        print(f"  -> TP: {tp}, FP: {fp}, FN: {fn}\n")

    # Calculate overall metrics
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print("=========================================")
    print("FINAL EVALUATION METRICS")
    print("=========================================")
    print(f"Total True Positives (TP) : {total_tp}")
    print(f"Total False Positives (FP): {total_fp}")
    print(f"Total False Negatives (FN): {total_fn}")
    print("-----------------------------------------")
    print(f"Precision : {precision:.2%} (Out of all matches the AI claimed, how many were correct?)")
    print(f"Recall    : {recall:.2%} (Out of all actual matches, how many did the AI find?)")
    print(f"F1-Score  : {f1_score:.2%} (Harmonic mean of Precision and Recall)")
    print("=========================================")

if __name__ == "__main__":
    evaluate()
