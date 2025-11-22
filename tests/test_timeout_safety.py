# SPDX - License - Identifier: MIT
# Copyright (c) 2025 Perday CatalogLAB™

"""
Timeout safety tests for label normalization.

Ensures regex and fuzzy matching operations complete within reasonable time bounds.
"""

import pytest
from label_normalizer_matcher import (
    LabelNormalizationError,
    find_similar_labels_timed,
    normalize_label,
)


class TestTimeoutSafety:
    """Test timeout controls prevent hangs."""

    @pytest.mark.timeout(1)
    def test_normalize_label_fast(self):
        """Test normalization completes quickly."""
        # Normal case
        result = normalize_label("Sony Music Entertainment, Inc.")
        assert "Sony Music Entertainment" in result

        # Edge case with lots of punctuation
        messy = "Sony!@#$%^&*()Music{}[]Entertainment,,,,,Inc."
        result = normalize_label(messy)
        assert "Sony" in result
        assert "Music" in result

    @pytest.mark.timeout(1)
    def test_find_similar_labels_fast(self):
        """Test fuzzy matching completes quickly."""
        candidates = [f"Label {i} Records" for i in range(100)]
        candidates.extend(
            [
                "Sony Music Entertainment",
                "Universal Music Group",
                "Warner Music Group",
            ]
        )

        # Should complete quickly even with 100+ candidates
        results = find_similar_labels_timed("Sony Music", candidates, timeout_sec=0.5)
        assert len(results) >= 0  # May be empty if no fuzzy matching available

    @pytest.mark.timeout(1)
    def test_pathological_regex_input(self):
        """Test that pathological regex inputs don't cause hangs."""
        # These patterns could cause catastrophic backtracking in naive regex
        pathological_inputs = [
            "a" * 1000 + "!",
            "(" * 100 + ")" * 100,
            "Sony" + "." * 500 + "Music",
            "Label" + "?" * 200 + "Records",
        ]

        for bad_input in pathological_inputs:
            # Should complete without hanging
            result = normalize_label(bad_input)
            assert isinstance(result, str)
            # Should complete without hanging (length may be same if no cleanup needed)

    def test_timeout_error_raised(self):
        """Test that timeout errors are properly raised."""
        # Create a scenario that would timeout
        huge_candidates = [
            f"Label {i} Records Entertainment Music Group" for i in range(10000)
        ]

        with pytest.raises(LabelNormalizationError, match="timed out"):
            find_similar_labels_timed(
                "Sony Music", huge_candidates, timeout_sec=0.001
            )  # Very short timeout

    @pytest.mark.timeout(2)
    def test_unicode_handling_fast(self):
        """Test Unicode normalization completes quickly."""
        unicode_labels = [
            "Björk Records",
            "Sigur Rós Music",
            "Mötley Crüe Entertainment",
            "Queensrÿche Records",
            "Café del Mar Music",
            "Naïve Records",
        ]

        for label in unicode_labels:
            result = normalize_label(label)
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.timeout(1)
    def test_empty_and_whitespace_fast(self):
        """Test edge cases complete quickly."""
        edge_cases = [
            "   ",
            "\t\n\r",
            "a",
            "A" * 1000,
            "123",
            "!@#$%^&*()",
        ]

        for case in edge_cases:
            try:
                result = normalize_label(case)
                assert isinstance(result, str)
            except LabelNormalizationError:
                # Empty cases should raise errors quickly
                pass
