"""
tests/test_matcher.py
======================
Unit tests for services/matcher.py.

Test strategy:
    - Happy-path: exact skill overlap → high score
    - Semantic: near-synonyms → should still match above threshold
    - Edge-case: empty resume skills, empty JD skills
    - Invalid-input: unrelated skill sets → low score

NOTE: These tests REQUIRE sentence-transformers to be installed.
If the package is not present, tests are skipped automatically.
"""

import pytest

# Skip entire module if sentence-transformers is not available
pytest.importorskip("sentence_transformers", reason="sentence-transformers not installed")

from services.matcher import compute_match, MATCH_THRESHOLD


class TestComputeMatchHappyPath:
    """Happy-path: good resume match → high scores."""

    def test_identical_skill_lists_score_100(self):
        """When resume skills exactly equal JD skills, score should be 100."""
        skills = ["python", "docker", "aws"]
        result = compute_match(skills, skills)
        assert result["score"] == 100
        assert result["missing_skills"] == []
        assert set(result["matched_skills"]) == set(skills)

    def test_full_overlap_returns_all_matched(self):
        """All JD skills present in resume → matched_skills = all JD skills."""
        resume = ["python", "flask", "postgresql", "docker", "aws"]
        jd = ["python", "flask", "docker"]
        result = compute_match(resume, jd)
        assert result["score"] == 100
        assert len(result["missing_skills"]) == 0

    def test_partial_overlap_returns_correct_score(self):
        """50% skill match → score should be approximately 50."""
        resume = ["python", "docker"]
        jd = ["python", "docker", "kubernetes", "terraform"]
        result = compute_match(resume, jd)
        # Exact score depends on semantic similarity; allow range
        assert 40 <= result["score"] <= 60

    def test_result_has_required_keys(self):
        """Result dict must contain all required keys."""
        result = compute_match(["python"], ["python", "java"])
        assert "score" in result
        assert "matched_skills" in result
        assert "missing_skills" in result
        assert "similarity_map" in result

    def test_score_is_integer(self):
        """Score must be an integer (0-100)."""
        result = compute_match(["python"], ["python"])
        assert isinstance(result["score"], int)
        assert 0 <= result["score"] <= 100


class TestComputeMatchSemantic:
    """Semantic matching: near-synonyms should still score high."""

    def test_react_and_reactjs_match(self):
        """'react' in resume should semantically match 'react.js' in JD."""
        result = compute_match(["react", "javascript"], ["react.js"])
        # The exact match depends on transformer similarity, but react/react.js
        # should score above threshold
        assert result["score"] >= 50  # Allow some slack for model variation

    def test_unrelated_skills_score_low(self):
        """Resume with only soft skills should score low against dev JD."""
        resume = ["leadership", "communication", "time management"]
        jd = ["python", "kubernetes", "terraform", "aws", "docker"]
        result = compute_match(resume, jd)
        assert result["score"] < 50


class TestComputeMatchEdgeCases:
    """Edge-case: empty or minimal inputs."""

    def test_empty_resume_skills_score_zero(self):
        """Empty resume skills → score of 0, all JD skills missing."""
        result = compute_match([], ["python", "docker"])
        assert result["score"] == 0
        assert set(result["missing_skills"]) == {"python", "docker"}
        assert result["matched_skills"] == []

    def test_empty_jd_skills_score_zero(self):
        """Empty JD skills → score 0 (nothing to match against)."""
        result = compute_match(["python", "docker"], [])
        assert result["score"] == 0

    def test_single_skill_exact_match(self):
        """Single skill matching itself → 100% score."""
        result = compute_match(["python"], ["python"])
        assert result["score"] == 100

    def test_similarity_map_populated(self):
        """similarity_map should have one entry per JD skill."""
        jd = ["python", "docker", "kubernetes"]
        result = compute_match(["python"], jd)
        assert set(result["similarity_map"].keys()) == set(jd)
