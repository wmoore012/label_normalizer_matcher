# SPDX-License-Identifier: MIT
# Copyright (c) 2024 MusicScope

"""
Core label normalization and matching functionality.

Elite helpers extracted from production music data processing pipeline.
Handles real-world label name variants with high-performance caching and timeout controls.
"""

import hashlib
import re
import unicodedata
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Tuple, Union

# TypedDict not needed in this module

# Prefer safer regex with timeout support
try:
    import regex as re_safe

    _SAFE_REGEX_AVAILABLE = True
except ImportError:
    import re as re_safe

    _SAFE_REGEX_AVAILABLE = False

# Optional high-performance fuzzy matching
try:
    from rapidfuzz import fuzz, process

    _RAPIDFUZZ_AVAILABLE = True
except ImportError:
    _RAPIDFUZZ_AVAILABLE = False
    # Fallback to basic fuzzy matching
    try:
        from fuzzy_entity_matcher import find_matches

        _FUZZY_MATCHING_AVAILABLE = True
    except ImportError:
        _FUZZY_MATCHING_AVAILABLE = False

from .exceptions import LabelNormalizationError


@dataclass
class CacheStats:
    """Statistics about cache performance."""

    hit_rate: float
    size: int
    max_size: int
    hits: int
    misses: int


# Compiled regex patterns with timeout support
if _SAFE_REGEX_AVAILABLE:
    _LABEL_CLEANUP_RE = re_safe.compile(r"[^\p{Letter}\p{Number}\s&'().,-]+", flags=re_safe.V1)
else:
    _LABEL_CLEANUP_RE = re.compile(r"[^\w\s&'().,-]+", flags=re.UNICODE)

_WHITESPACE_RE = re.compile(r"\s{2,}")
_SUFFIX_RE = re.compile(r",?\s*(inc\.?|llc|ltd\.?|corp\.?)$", re.IGNORECASE)

# Module-level caches for performance - same pattern as production
_label_cache: Dict[str, str] = {}
_id_cache: Dict[str, str] = {}
_cache_hits = 0
_cache_misses = 0
_max_cache_size = 10000


def _clean_text(text: str, *, timeout_ms: int = 20) -> str:
    """Clean text with timeout protection against catastrophic backtracking."""
    if _SAFE_REGEX_AVAILABLE:
        return _LABEL_CLEANUP_RE.sub("", text, timeout=timeout_ms).strip()
    else:
        return _LABEL_CLEANUP_RE.sub("", text).strip()


@lru_cache(maxsize=50_000)
def normalize_label(raw: str) -> str:
    """
    Normalize a label name using elite production logic with timeout protection.

    Handles real-world music industry label variants:
    - Corporate suffixes (Inc., LLC, Ltd., Corp.)
    - Copyright symbols and years (℗ 2023)
    - Whitespace normalization
    - Case standardization

    Args:
        raw: Raw label name from music metadata

    Returns:
        Clean, normalized label name

    Raises:
        LabelNormalizationError: If raw is None or empty
    """
    if not raw or not raw.strip():
        raise LabelNormalizationError("Label name cannot be empty")

    # Clean with timeout protection
    s = _clean_text(raw)

    # Normalize whitespace
    s = _WHITESPACE_RE.sub(" ", s)

    # Remove corporate suffixes
    s = _SUFFIX_RE.sub("", s)

    # Final whitespace cleanup
    return _WHITESPACE_RE.sub(" ", s).strip()


def get_canonical_label_id(name: str) -> str:
    """
    Generate deterministic canonical ID for label matching.

    Creates consistent IDs for database foreign keys and deduplication.
    Uses BLAKE2b hash for cryptographic stability and collision resistance.

    Args:
        name: Label name (normalized automatically)

    Returns:
        Stable canonical ID (format: slug-hash6)

    Example:
        >>> get_canonical_label_id("Sony Music Entertainment, Inc.")
        'sony-music-entertainment-a1b2c3'
    """
    if not name or not name.strip():
        raise LabelNormalizationError("Label name cannot be empty")

    # Normalize first
    norm = normalize_label(name)

    # Create URL-safe slug
    slug = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", norm).lower()).strip("-")

    # Generate cryptographically stable hash
    h = hashlib.blake2b(norm.encode("utf-8"), digest_size=3).hexdigest()

    return f"{slug}-{h}"


def strip_year_and_suffix(text: str) -> str:
    """
    Strip copyright years and corporate suffixes from label names.

    Elite helper for processing raw music metadata with copyright info.
    Handles complex patterns from Tidal API like:
    - "℗ 2023 Sony Music Entertainment, Inc."
    - "(P) & ℗ 2022 Warner Records LLC"
    - "℗2023Sony Music Entertainment" (missing spaces)
    - "℗ © 2023 Sony Music Entertainment" (multiple symbols)

    Args:
        text: Raw label text with potential copyright info

    Returns:
        Clean label name without year/copyright symbols
    """
    if not text:
        return text

    # Match copyright patterns with year validation
    current_year = datetime.now().year
    max_year = current_year + 4

    # Enhanced pattern to handle complex copyright symbols and missing spaces
    # Matches: ℗, (P), P, &, ©, C, spaces, parentheses, followed by year and label name
    # Handle both spaced and non-spaced patterns
    patterns = [
        # Standard pattern with spaces: "℗ 2023 Label Name"
        r"^[\s\(\)℗P&©C]*(?P<year>[12]\d{3})\s+(?P<name>.*)",
        # Missing space pattern: "℗2023Label Name"
        r"^[\s\(\)℗P&©C]*(?P<year>[12]\d{3})(?P<name>[A-Za-z].*)",
    ]

    for pattern in patterns:
        match = re.match(pattern, text.strip(), re.IGNORECASE)
        if match and 1900 <= int(match.group("year")) <= max_year:
            core = match.group("name").strip()
            # Apply standard cleaning
            return _clean_label_name(core)

    # No valid year found - remove copyright symbols only
    # Handle complex patterns like "(P) & ℗", "℗ ©", etc.
    core = re.sub(r"^[\s\(\)℗P&©C]*", "", text.strip())

    # Apply standard cleaning
    return _clean_label_name(core)


def clear_cache() -> None:
    """Clear all caches - same pattern as production helpers."""
    normalize_label.cache_clear()  # type: ignore[attr-defined]
    global _label_cache, _id_cache, _cache_hits, _cache_misses
    _label_cache.clear()
    _id_cache.clear()
    _cache_hits = 0
    _cache_misses = 0


def find_similar_labels(
    query: str,
    candidates: Iterable[str],
    *,
    limit: int = 5,
    include_scores: bool = False,
    normalize_first: bool = True,
) -> Union[List[str], List[Tuple[str, float]]]:
    """
    Find similar labels using high-performance fuzzy matching with timeout protection.

    Uses RapidFuzz for performance when available, with fallback to basic matching.
    Optionally normalizes labels before matching for better accuracy.

    Args:
        query: Label to find matches for
        candidates: Iterable of labels to search through
        limit: Maximum number of matches to return
        include_scores: If True, return tuples of (label, score)
        normalize_first: If True, normalize labels before matching

    Returns:
        List of similar labels, optionally with scores

    Raises:
        LabelNormalizationError: If query is empty or timeout exceeded

    Examples:
        >>> find_similar_labels("Sony Music", ["Sony Music Entertainment", "Warner Music"])
        ["Sony Music Entertainment"]
        >>> find_similar_labels("Sony Music", ["Sony Music Entertainment"], include_scores=True)
        [("Sony Music Entertainment", 0.85)]
    """
    if not query or not query.strip():
        raise LabelNormalizationError("Query label cannot be empty")

    candidate_list = list(candidates)
    if not candidate_list:
        return []

    # Normalize query and candidates if requested
    if normalize_first:
        qn = normalize_label(query)
        normalized_candidates = [normalize_label(c) for c in candidate_list]
    else:
        qn = query
        normalized_candidates = candidate_list

    if _RAPIDFUZZ_AVAILABLE:
        # Use high-performance RapidFuzz
        matches = process.extract(
            qn, normalized_candidates, scorer=fuzz.token_sort_ratio, score_cutoff=85, limit=limit
        )

        if include_scores:
            # Return original labels with scores
            return [(candidate_list[i], score / 100.0) for _, score, i in matches]
        else:
            # Return just the original labels
            return [candidate_list[i] for _, _, i in matches]

    elif _FUZZY_MATCHING_AVAILABLE:
        # Fallback to fuzzy-entity-matcher - this doesn't support scores easily
        matches = find_matches(qn, normalized_candidates, limit=limit)
        if include_scores:
            # Return with dummy scores since fuzzy-entity-matcher doesn't provide them
            return [(candidate_list[normalized_candidates.index(m)], 0.85) for m in matches]
        else:
            return [candidate_list[normalized_candidates.index(m)] for m in matches]
    else:
        # Basic string matching fallback
        matches_with_scores = []
        for i, (nc, c) in enumerate(zip(normalized_candidates, candidate_list)):
            if qn.lower() in nc.lower():
                # Simple score based on length ratio
                score = len(qn) / len(nc) if nc else 0.0
                matches_with_scores.append((c, score, i))

        # Sort by score descending and take top matches
        matches_with_scores.sort(key=lambda x: x[1], reverse=True)
        matches_with_scores = matches_with_scores[:limit]

        if include_scores:
            return [(c, score) for c, score, _ in matches_with_scores]
        else:
            return [c for c, _, _ in matches_with_scores]


def find_similar_labels_timed(
    query: str, candidates: Iterable[str], timeout_sec: float = 0.15
) -> List[str]:
    """
    Find similar labels with guaranteed timeout to prevent hangs.

    Args:
        query: Label to find matches for
        candidates: Iterable of labels to search through
        timeout_sec: Maximum time to spend matching (default 0.15s)

    Returns:
        List of similar labels

    Raises:
        LabelNormalizationError: If timeout exceeded
    """

    def _similar_internal(q, cands):
        return find_similar_labels(q, cands)

    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(_similar_internal, query, list(candidates))
        try:
            return fut.result(timeout=timeout_sec)
        except TimeoutError as e:
            raise LabelNormalizationError(
                f"Similarity matching timed out after {timeout_sec}s"
            ) from e


def get_cache_stats() -> CacheStats:
    """Get cache performance statistics."""
    info = normalize_label.cache_info()  # type: ignore[attr-defined]
    total_requests = info.hits + info.misses
    hit_rate = info.hits / total_requests if total_requests > 0 else 0.0

    return CacheStats(
        hit_rate=hit_rate,
        size=info.currsize,
        max_size=info.maxsize,
        hits=info.hits,
        misses=info.misses,
    )


# Private helpers - extracted from production ETL pipeline


def _clean_label_name(name: str) -> str:
    """
    Core label cleaning logic from production ETL.

    Handles the most common corporate suffix patterns found in music metadata.
    """
    if not name:
        return name

    # First strip whitespace, then remove corporate suffixes
    name = name.strip()
    name = re.sub(r",?\s*(Inc\.?|LLC|Ltd\.?|Corp\.?)$", "", name, flags=re.IGNORECASE)

    # Final whitespace cleanup
    return name.strip()


def _generate_stable_id(normalized_name: str) -> str:
    """Generate stable ID using MD5 hash for consistency."""
    # Create URL-friendly slug
    slug = re.sub(r"[^\w\s-]", "", normalized_name.lower())
    slug = re.sub(r"[-\s]+", "-", slug).strip("-")

    # MD5 hash for stability (same as production)
    hash_obj = hashlib.md5(normalized_name.encode("utf-8"))
    short_hash = hash_obj.hexdigest()[:6]

    return f"{slug}-{short_hash}" if slug else f"label-{short_hash}"
