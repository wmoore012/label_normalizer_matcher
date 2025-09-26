# SPDX-License-Identifier: MIT
# Copyright (c) 2024 MusicScope

"""
Integration tests using real MySQL data.

Tests the label normalizer against actual music industry data
from our production database.
"""

import os
from typing import List, Tuple

import pytest

# Skip integration tests if no database available
pytest_plugins = []
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import Engine

    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

from label_normalizer_matcher import (
    clear_cache,
    find_similar_labels,
    get_canonical_label_id,
    normalize_label,
)


def get_test_engine() -> Engine:
    """Get database engine for testing."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Try to construct from individual env vars
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "3306")
        user = os.getenv("DB_USER", "root")
        password = os.getenv("DB_PASSWORD", "")
        database = os.getenv("DB_NAME", "icatalog_public")

        if not password:
            # If no password is set, skip database tests
            raise ConnectionError("No database password configured")

        database_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

    return create_engine(database_url)


@pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database dependencies not available")
class TestRealDatabaseIntegration:
    """Test against real label data from MySQL."""

    def setup_method(self):
        """Clear cache and setup database connection."""
        clear_cache()
        try:
            self.engine = get_test_engine()
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def get_sample_labels(self, limit: int = 50) -> List[Tuple[int, str]]:
        """Get sample labels from the database."""
        with self.engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT label_id, label_name
                FROM labels
                WHERE label_name IS NOT NULL
                AND label_name != ''
                ORDER BY label_id
                LIMIT :limit
            """
                ),
                {"limit": limit},
            )
            return [(row[0], row[1]) for row in result.fetchall()]

    def get_labels_with_suffixes(self, limit: int = 20) -> List[Tuple[int, str]]:
        """Get labels with corporate suffixes."""
        with self.engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT label_id, label_name
                FROM labels
                WHERE label_name REGEXP '(Inc\\.?|LLC|Ltd\\.?|Corp\\.?)$'
                ORDER BY label_id
                LIMIT :limit
            """
                ),
                {"limit": limit},
            )
            return [(row[0], row[1]) for row in result.fetchall()]

    def test_normalize_real_labels(self):
        """Test normalization on real label data."""
        labels = self.get_sample_labels(20)
        assert len(labels) > 0, "No labels found in database"

        for label_id, label_name in labels:
            # Should not raise exceptions
            normalized = normalize_label(label_name)

            # Basic sanity checks
            assert isinstance(normalized, str)
            assert len(normalized) > 0

            # Should remove trailing whitespace
            assert normalized == normalized.strip()

            print(f"Label {label_id}: '{label_name}' -> '{normalized}'")

    def test_normalize_labels_with_suffixes(self):
        """Test normalization on labels with corporate suffixes."""
        labels = self.get_labels_with_suffixes(10)

        if len(labels) == 0:
            pytest.skip("No labels with corporate suffixes found")

        for label_id, label_name in labels:
            normalized = normalize_label(label_name)

            # Should remove common suffixes
            assert not normalized.endswith(", Inc.")
            assert not normalized.endswith(" Inc.")
            assert not normalized.endswith(", LLC")
            assert not normalized.endswith(" LLC")
            assert not normalized.endswith(", Ltd.")
            assert not normalized.endswith(" Ltd.")

            print(f"Suffix removal {label_id}: '{label_name}' -> '{normalized}'")

    def test_canonical_ids_for_real_labels(self):
        """Test canonical ID generation for real labels."""
        labels = self.get_sample_labels(10)
        assert len(labels) > 0, "No labels found in database"

        ids_generated = set()

        for label_id, label_name in labels:
            canonical_id = get_canonical_label_id(label_name)

            # Basic format checks
            assert isinstance(canonical_id, str)
            assert len(canonical_id) > 0
            assert "-" in canonical_id  # Should have slug-hash format

            # Should be unique
            assert canonical_id not in ids_generated, f"Duplicate ID: {canonical_id}"
            ids_generated.add(canonical_id)

            print(f"ID for {label_id}: '{label_name}' -> '{canonical_id}'")

    def test_performance_with_real_data(self):
        """Test performance with real database labels."""
        labels = self.get_sample_labels(100)

        if len(labels) < 10:
            pytest.skip("Not enough labels for performance test")

        # Test normalization performance
        import time

        start_time = time.time()

        for label_id, label_name in labels:
            normalize_label(label_name)

        normalization_time = time.time() - start_time

        # Test canonical ID performance
        start_time = time.time()

        for label_id, label_name in labels:
            get_canonical_label_id(label_name)

        id_generation_time = time.time() - start_time

        print(f"Normalized {len(labels)} labels in {normalization_time:.3f}s")
        print(f"Generated {len(labels)} IDs in {id_generation_time:.3f}s")

        # Performance assertions (should be fast)
        assert normalization_time < 1.0, "Normalization too slow"
        assert id_generation_time < 1.0, "ID generation too slow"

    def test_cache_effectiveness_with_real_data(self):
        """Test cache effectiveness with real data patterns."""
        labels = self.get_sample_labels(20)

        if len(labels) < 5:
            pytest.skip("Not enough labels for cache test")

        # Clear cache and get baseline
        clear_cache()

        # First pass - should all be cache misses
        for label_id, label_name in labels:
            normalize_label(label_name)

        from label_normalizer_matcher import get_cache_stats

        stats_after_first = get_cache_stats()

        # Second pass - should all be cache hits
        for label_id, label_name in labels:
            normalize_label(label_name)

        stats_after_second = get_cache_stats()

        # Verify cache is working
        assert stats_after_second.hits > stats_after_first.hits
        assert stats_after_second.hit_rate > 0.5  # Should have good hit rate

        print(f"Cache stats: {stats_after_second.hits} hits, {stats_after_second.misses} misses")
        print(f"Hit rate: {stats_after_second.hit_rate:.2%}")

    def test_deduplication_potential(self):
        """Test how many labels could be deduplicated."""
        labels = self.get_sample_labels(50)

        if len(labels) < 10:
            pytest.skip("Not enough labels for deduplication test")

        # Group by normalized name
        normalized_groups = {}

        for label_id, label_name in labels:
            normalized = normalize_label(label_name)
            if normalized not in normalized_groups:
                normalized_groups[normalized] = []
            normalized_groups[normalized].append((label_id, label_name))

        # Find potential duplicates
        potential_duplicates = {
            normalized: group for normalized, group in normalized_groups.items() if len(group) > 1
        }

        if potential_duplicates:
            print(f"Found {len(potential_duplicates)} potential duplicate groups:")
            for normalized, group in potential_duplicates.items():
                print(f"  '{normalized}': {[name for _, name in group]}")

        # This is informational - we expect some duplicates in real data
        total_labels = len(labels)
        unique_normalized = len(normalized_groups)
        dedup_potential = total_labels - unique_normalized

        print(f"Deduplication potential: {dedup_potential}/{total_labels} labels")


@pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database dependencies not available")
class TestSpecificLabelPatterns:
    """Test specific patterns found in our music database."""

    def setup_method(self):
        """Setup database connection."""
        clear_cache()
        try:
            self.engine = get_test_engine()
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_major_label_patterns_in_db(self):
        """Test major label patterns that exist in our database."""
        with self.engine.connect() as conn:
            # Look for Sony variants
            sony_labels = conn.execute(
                text(
                    """
                SELECT label_name FROM labels
                WHERE label_name LIKE '%Sony%'
                LIMIT 5
            """
                )
            ).fetchall()

            for (label_name,) in sony_labels:
                normalized = normalize_label(label_name)
                # Should clean up corporate suffixes
                assert "Sony" in normalized
                print(f"Sony variant: '{label_name}' -> '{normalized}'")

            # Look for Warner variants
            warner_labels = conn.execute(
                text(
                    """
                SELECT label_name FROM labels
                WHERE label_name LIKE '%Warner%'
                LIMIT 5
            """
                )
            ).fetchall()

            for (label_name,) in warner_labels:
                normalized = normalize_label(label_name)
                assert "Warner" in normalized
                print(f"Warner variant: '{label_name}' -> '{normalized}'")

    def test_fuzzy_matching_with_real_labels(self):
        """Test fuzzy matching functionality with real database labels."""
        labels = self.get_sample_labels(20)

        if len(labels) < 5:
            pytest.skip("Not enough labels for fuzzy matching test")

        # Test fuzzy matching between labels
        label_names = [name for _, name in labels[:10]]

        if len(label_names) >= 2:
            # Test finding similar labels
            query_label = label_names[0]
            candidates = label_names[1:]

            # This should not raise exceptions even if no fuzzy matcher is available
            similar = find_similar_labels(query_label, candidates, threshold=0.6)

            # Should return a list (empty if no fuzzy matcher available)
            assert isinstance(similar, list)

            print(f"Similar to '{query_label}': {similar}")

            # Test with scores
            similar_with_scores = find_similar_labels(
                query_label, candidates, threshold=0.6, include_scores=True
            )

            assert isinstance(similar_with_scores, list)

            if similar_with_scores:
                # Should be tuples if include_scores=True
                assert all(
                    isinstance(item, tuple) and len(item) == 2 for item in similar_with_scores
                )
                print(f"Similar with scores: {similar_with_scores}")

    def test_copyright_patterns_in_metadata(self):
        """Test copyright patterns that might exist in metadata."""
        # This would test against actual copyright strings if they exist
        # in our database metadata fields
        # Implementation depends on available metadata fields
