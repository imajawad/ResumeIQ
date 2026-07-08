"""
tests/test_extractor.py
========================
Unit tests for services/skill_extractor.py.

Test strategy:
    - Happy-path: text with known skills → all skills identified
    - Edge-case: empty string, whitespace-only, numbers-only
    - Invalid-input: None-like empty string input
    - Variation tests: skill aliases and case sensitivity
"""

import os
import pytest
from services.skill_extractor import extract_skills

if not os.getenv("GROQ_API_KEY"):
    pytest.skip("Skipping LLM tests in CI because GROQ_API_KEY is not set", allow_module_level=True)


class TestExtractSkillsHappyPath:
    """Happy-path tests: known skills should be identified correctly."""

    def test_single_programming_language(self):
        """A text containing 'Python' should return ['python']."""
        result = extract_skills("I have 5 years of Python experience.")
        assert "python" in result

    def test_multiple_languages(self):
        """Multiple programming languages in text should all be detected."""
        text = "Experience with Python, Java, and JavaScript."
        result = extract_skills(text)
        assert "python" in result
        assert "java" in result
        assert "javascript" in result

    def test_compound_skill_phrase(self):
        """Multi-word skills like 'machine learning' should be identified."""
        text = "Background in machine learning and deep learning."
        result = extract_skills(text)
        assert "machine learning" in result

    def test_cloud_skills_detected(self):
        """AWS, Docker, Kubernetes should be identified from tech resume text."""
        text = "Deployed applications on AWS using Docker and Kubernetes."
        result = extract_skills(text)
        assert "aws" in result
        assert "docker" in result
        assert "kubernetes" in result

    def test_result_is_sorted(self):
        """Output list should be sorted alphabetically."""
        text = "Python, AWS, Docker, React"
        result = extract_skills(text)
        assert result == sorted(result)

    def test_result_is_deduplicated(self):
        """Duplicate mentions of the same skill should appear only once."""
        text = "Python Python Python Python developer Python"
        result = extract_skills(text)
        assert result.count("python") == 1

    def test_case_insensitive_detection(self):
        """Skills should be detected regardless of casing."""
        text = "PYTHON developer with REACT.JS and AWS skills"
        result = extract_skills(text)
        assert "python" in result
        assert "aws" in result

    def test_framework_detection(self):
        """Web frameworks like Flask, Django should be detected."""
        text = "Built REST APIs using Flask and Django."
        result = extract_skills(text)
        assert "flask" in result
        assert "django" in result


class TestExtractSkillsEdgeCases:
    """Edge-case tests: boundary conditions and minimal inputs."""

    def test_empty_string_returns_empty_list(self):
        """Empty string input should return an empty list."""
        assert extract_skills("") == []

    def test_whitespace_only_returns_empty_list(self):
        """Whitespace-only input should return an empty list."""
        assert extract_skills("   \n\t  ") == []

    def test_numbers_only_returns_empty_list(self):
        """Text with only numbers and no skill keywords → empty list."""
        result = extract_skills("1234 5678 9012")
        assert result == []

    def test_short_text_with_one_skill(self):
        """A single-word skill text should still be identified."""
        result = extract_skills("Python")
        assert "python" in result

    def test_no_skills_in_generic_text(self):
        """Generic English prose with no tech skills → empty or very short list."""
        text = "The quick brown fox jumps over the lazy dog."
        result = extract_skills(text)
        # Result might not be perfectly empty depending on coincidental tokens,
        # but should contain no recognised technical skills
        tech_skills = {"python", "java", "aws", "docker", "kubernetes", "react"}
        assert len(tech_skills.intersection(set(result))) == 0


class TestExtractSkillsInvalidInput:
    """Invalid-input tests: graceful handling of bad inputs."""

    def test_none_equivalent_empty_string(self):
        """None-like inputs should return empty list, not raise exceptions."""
        assert extract_skills("") == []

    def test_very_long_text_does_not_error(self):
        """Very long text should be processed without error."""
        long_text = ("Python AWS Docker Kubernetes React Flask SQL " * 500)
        result = extract_skills(long_text)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_special_characters_text(self):
        """Text with lots of special characters should not raise exceptions."""
        text = "###!!!@@@Python<<<>>>AWS[[[Docker]]]"
        result = extract_skills(text)
        assert isinstance(result, list)


class TestExtractSkillsVariations:
    """Tests for skill aliases and near-variants."""

    def test_react_and_reactjs_both_detected(self):
        """Both 'React' and 'React.js' tokens should yield a react skill."""
        text1 = "Experience with React"
        text2 = "Experience with React.js"
        r1 = extract_skills(text1)
        r2 = extract_skills(text2)
        # At least one variant should register as a skill
        assert "react" in r1 or "react.js" in r1
        assert "react" in r2 or "react.js" in r2

    def test_agile_methodology_detected(self):
        """'agile' as standalone token should be detected."""
        result = extract_skills("Worked in an agile development team.")
        assert "agile" in result
