"""
tests/test_gap_analysis.py
===========================
Unit tests for gap analysis logic and services/recommender.py.

Gap analysis is derived from the compute_match() output (missing_skills).
These tests verify that missing_skills = JD skills − matched skills,
and that recommendations are returned for known skill gaps.
"""

import os
import pytest
from services.recommender import get_recommendations

if not os.getenv("GROQ_API_KEY"):
    pytest.skip("Skipping LLM tests in CI because GROQ_API_KEY is not set", allow_module_level=True)


class TestGetRecommendationsHappyPath:
    """Happy-path: known missing skills → relevant course links returned."""

    def test_python_skill_gap_returns_recommendation(self):
        """'python' as missing skill → returns a recommendation with a URL."""
        result = get_recommendations(["python"])
        assert len(result) >= 1
        rec = result[0]
        assert rec["skill"] == "python"
        assert "url" in rec
        assert rec["url"].startswith("http")

    def test_multiple_skills_return_multiple_recs(self):
        """Multiple known skills → one recommendation each (where available)."""
        skills = ["python", "docker", "aws", "machine learning"]
        result = get_recommendations(skills)
        assert len(result) >= 3  # At least 3 of the 4 should have courses

    def test_recommendation_has_required_keys(self):
        """Each recommendation must contain all required fields."""
        result = get_recommendations(["python"])
        assert len(result) > 0
        rec = result[0]
        assert all(key in rec for key in ["skill", "title", "url", "platform", "level"])

    def test_platform_is_valid(self):
        """Platform field should be one of the known course providers."""
        valid_platforms = {"Coursera", "YouTube", "freeCodeCamp"}
        result = get_recommendations(["python", "docker", "machine learning"])
        for rec in result:
            assert rec["platform"] in valid_platforms

    def test_level_is_valid(self):
        """Level field should be Beginner, Intermediate, or Advanced."""
        valid_levels = {"Beginner", "Intermediate", "Advanced"}
        result = get_recommendations(["python", "aws"])
        for rec in result:
            assert rec["level"] in valid_levels


class TestGetRecommendationsEdgeCases:
    """Edge-case: empty inputs and skills with no course."""

    def test_empty_missing_skills_returns_empty_list(self):
        """No missing skills → empty recommendations list."""
        result = get_recommendations([])
        assert result == []

    def test_unknown_skill_returns_no_recommendation(self):
        """A made-up skill name should return no recommendation (not error)."""
        result = get_recommendations(["xyzzy_unknown_skill_12345"])
        assert result == []

    def test_duplicate_skills_deduplicated_by_url(self):
        """Same skill listed twice should not produce duplicate course URLs."""
        result = get_recommendations(["python", "python"])
        urls = [r["url"] for r in result]
        assert len(urls) == len(set(urls))


class TestGetRecommendationsAliases:
    """Tests for keyword alias resolution."""

    def test_react_js_alias_resolves(self):
        """'react.js' should resolve via alias to a React course."""
        result = get_recommendations(["react.js"])
        assert len(result) > 0

    def test_nodejs_alias_resolves(self):
        """'nodejs' should resolve to a Node.js course."""
        result = get_recommendations(["nodejs"])
        assert len(result) > 0

    def test_sklearn_alias_resolves(self):
        """'sklearn' should resolve to a machine learning course."""
        result = get_recommendations(["sklearn"])
        assert len(result) > 0


class TestGapAnalysisLogic:
    """Verify gap logic: missing = JD − matched (integration-style)."""

    def test_gap_equals_jd_minus_matched(self):
        """missing_skills + matched_skills must equal jd_skills (set union)."""
        pytest.importorskip("sentence_transformers")
        from services.matcher import compute_match

        resume = ["python", "docker"]
        jd = ["python", "docker", "kubernetes", "terraform"]
        result = compute_match(resume, jd)

        combined = set(result["matched_skills"]) | set(result["missing_skills"])
        assert combined == set(jd)

    def test_no_false_positives_in_matched(self):
        """Skills NOT in JD should never appear in matched_skills."""
        pytest.importorskip("sentence_transformers")
        from services.matcher import compute_match

        resume = ["python", "docker", "kubernetes"]
        jd = ["python"]
        result = compute_match(resume, jd)

        # matched_skills should only contain JD skills
        for skill in result["matched_skills"]:
            assert skill in jd
