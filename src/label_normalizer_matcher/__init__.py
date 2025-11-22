# SPDX - License - Identifier: MIT
# Copyright (c) 2025 Perday CatalogLAB™

"""
Label Normalizer Matcher - Elite music industry label normalization.

Extracted from production music data pipeline. Handles real - world label variants
with high - performance caching, stable ID generation, and fuzzy matching.

Example:
    >>> from label_normalizer_matcher import normalize_label, get_canonical_label_id, find_similar_labels
    >>> normalize_label("Sony Music Entertainment, Inc.")
    'Sony Music Entertainment'
    >>> get_canonical_label_id("Sony Music Entertainment")
    'sony - music - entertainment - a1b2c3'
    >>> find_similar_labels("Sony Music", ["Sony Music Entertainment", "Warner Music"])
    ['Sony Music Entertainment']
"""

__version__ = "0.1.0"

# Dynamic version from installed package metadata
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("label - normalizer - matcher")
except PackageNotFoundError:  # local dev
    pass  # Use the static version above

from .core import (
    CacheStats,
    clear_cache,
    find_similar_labels,
    find_similar_labels_timed,
    get_cache_stats,
    get_canonical_label_id,
    normalize_label,
    strip_year_and_suffix,
)
from .exceptions import LabelNormalizationError, MissingExtraError, TimeoutExceededError

__all__ = [
    "normalize_label",
    "get_canonical_label_id",
    "strip_year_and_suffix",
    "find_similar_labels",
    "find_similar_labels_timed",
    "clear_cache",
    "get_cache_stats",
    "LabelNormalizationError",
    "MissingExtraError",
    "TimeoutExceededError",
    "CacheStats",
    "__version__",
]

# Expose benchmarks only if installed
try:
    from .benchmarks import (
        BenchmarkResult,
        LabelNormalizerBenchmark,
        generate_realistic_labels,
    )

    __all__ += [
        "LabelNormalizerBenchmark",
        "BenchmarkResult",
        "generate_realistic_labels",
    ]
except Exception:  # no - op: keep runtime light
    pass
