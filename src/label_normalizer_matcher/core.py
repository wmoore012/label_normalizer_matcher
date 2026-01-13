# SPDX - License - Identifier: MIT
# Copyright (c) 2025 Perday CatalogLAB™

"""Core label normalization and fuzzy matching utilities.

This module provides the public API used by tests and by
:mod:`label_normalizer_matcher.__init__`:

- ``normalize_label``
- ``get_canonical_label_id``
- ``strip_year_and_suffix``
- ``find_similar_labels`` / ``find_similar_labels_timed``
- cache inspection helpers (``clear_cache``, ``get_cache_stats``).

The implementation is intentionally lightweight and deterministic so it can
run inside CI without external services or databases.
"""

from __future__ import annotations

import hashlib
import re
import time
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Optional, Union

from .exceptions import LabelNormalizationError, TimeoutExceededError

# ---------------------------------------------------------------------------
# Cache tracking
# ---------------------------------------------------------------------------


@dataclass
class CacheStats:
    """Simple cache statistics exposed to benchmarks and tests."""

    hits: int = 0
    misses: int = 0
    size: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


# Single cache shared across normalization / ID helpers
_CACHE: dict[tuple[str, str], str] = {}
_CACHE_STATS = CacheStats()


def clear_cache() -> None:
    """Clear all cached entries and reset statistics.

    This is used heavily in tests and benchmarks to measure cold/hot
    performance, so we keep the semantics very explicit.
    """

    _CACHE.clear()
    _CACHE_STATS.hits = 0
    _CACHE_STATS.misses = 0
    _CACHE_STATS.size = 0


def get_cache_stats() -> CacheStats:
    """Return a snapshot of current cache statistics.

    A new :class:`CacheStats` instance is returned on each call so callers
    cannot mutate internal counters.
    """

    return CacheStats(_CACHE_STATS.hits, _CACHE_STATS.misses, len(_CACHE))


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


_CORPORATE_SUFFIX_RE = re.compile(r",?\s*(Inc\.?|LLC|Ltd\.?|Corp\.?)$", re.IGNORECASE)


def strip_year_and_suffix(text: str) -> str:
    """Strip leading copyright year/symbols and trailing corporate suffixes.

    This mirrors the behaviour used in the production ETL helpers and is
    purposely conservative – if no year is detected we simply return the
    stripped text with common corporate suffixes removed.
    """

    if not text:
        return text

    m = re.match(
        r"^[\s\(\)℗]*(?P<year>[12]\d{3})\s+(?P<name>.*)", text.strip(), re.IGNORECASE
    )
    if m and 1900 <= int(m.group("year")) <= time.localtime().tm_year + 4:
        core = m.group("name").strip()
    else:
        core = text.strip()

    return _CORPORATE_SUFFIX_RE.sub("", core).strip()


def _normalize_for_match(text: str) -> str:
    """Internal normalization used for matching and ID generation."""

    # First remove copyright/year noise and suffixes
    core = strip_year_and_suffix(text)
    # Basic whitespace + unicode cleanup
    core = " ".join(core.split())
    core = unicodedata.normalize("NFKD", core).encode("ascii", "ignore").decode("ascii")
    core = core.lower()
    core = re.sub(r"[^a-z0-9]+", " ", core)
    return " ".join(core.split())


def normalize_label(label: str) -> str:
    """Normalize a raw label string into a canonical display form.

    The function is deliberately tolerant – for clearly empty inputs we raise
    :class:`LabelNormalizationError`, otherwise we return a best-effort
    normalized string.
    """

    if not isinstance(label, str):  # defensive, keeps error surface explicit
        raise LabelNormalizationError("label must be a string")

    raw = label.strip()
    if not raw:
        raise LabelNormalizationError("label is empty after stripping")

    cache_key = ("normalize", raw)
    if cache_key in _CACHE:
        _CACHE_STATS.hits += 1
        return _CACHE[cache_key]

    _CACHE_STATS.misses += 1

    cleaned = strip_year_and_suffix(raw)
    cleaned = " ".join(cleaned.split())
    if not cleaned:
        raise LabelNormalizationError("label is empty after normalization")

    _CACHE[cache_key] = cleaned
    _CACHE_STATS.size = len(_CACHE)
    return cleaned


def _slugify_label(text: str) -> str:
    cleaned = _normalize_for_match(text)
    slug = re.sub(r"[^a-z0-9]+", "-", cleaned).strip("-")
    return slug or "label"


def get_canonical_label_id(label: str) -> str:
    """Generate a stable canonical ID for a label.

    IDs are derived from the normalized label plus an MD5 hash suffix. This
    keeps IDs deterministic across runs without leaking implementation details
    into tests.
    """

    normalized = normalize_label(label)

    cache_key = ("id", normalized)
    if cache_key in _CACHE:
        _CACHE_STATS.hits += 1
        return _CACHE[cache_key]

    _CACHE_STATS.misses += 1

    slug = _slugify_label(normalized)
    digest = hashlib.md5(normalized.encode("utf-8")).hexdigest()[:8]
    canonical_id = f"{slug}-{digest}"

    _CACHE[cache_key] = canonical_id
    _CACHE_STATS.size = len(_CACHE)
    return canonical_id


# ---------------------------------------------------------------------------
# Fuzzy matching
# ---------------------------------------------------------------------------


def find_similar_labels(
    query: str,
    candidates: Iterable[str],
    threshold: float = 0.8,
    *,
    include_scores: bool = False,
    limit: Optional[int] = None,
) -> Union[list[str], list[tuple[str, float]]]:
    """Return labels similar to *query* from *candidates*.

    The implementation uses a lightweight similarity heuristic based on
    normalized strings and does not depend on any external libraries.
    """

    if threshold < 0.0 or threshold > 1.0:
        raise ValueError("threshold must be between 0.0 and 1.0")

    cand_list = [c for c in candidates if isinstance(c, str) and c]
    if not cand_list:
        return [] if not include_scores else []

    q = _normalize_for_match(query)

    scored: list[tuple[str, float]] = []
    for c in cand_list:
        c_norm = _normalize_for_match(c)
        # Jaccard-like token overlap
        q_tokens = set(q.split())
        c_tokens = set(c_norm.split())
        if not q_tokens or not c_tokens:
            score = 0.0
        else:
            intersection = len(q_tokens & c_tokens)
            union = len(q_tokens | c_tokens)
            score = intersection / union
        if score >= threshold:
            scored.append((c, float(score)))

    scored.sort(key=lambda t: t[1], reverse=True)

    if limit is not None and isinstance(limit, int) and limit > 0:
        scored = scored[:limit]

    if include_scores:
        return scored
    return [label for (label, _score) in scored]


def find_similar_labels_timed(
    query: str,
    candidates: Iterable[str],
    *,
    threshold: float = 0.8,
    timeout_sec: float = 0.5,
    include_scores: bool = False,
    limit: Optional[int] = None,
) -> Union[list[str], list[tuple[str, float]]]:
    """Time-bounded variant of :func:`find_similar_labels`.

    If the operation exceeds ``timeout_sec`` a :class:`LabelNormalizationError`
    (via :class:`TimeoutExceededError`) is raised with a message containing
    ``"timed out"`` as required by tests.
    """

    start = time.perf_counter()
    deadline = start + max(timeout_sec, 0.0)

    # Materialise candidates once so we can iterate multiple times if needed
    cand_list = list(candidates)

    scored: list[tuple[str, float]] = []
    q = _normalize_for_match(query)
    q_tokens = set(q.split())

    for c in cand_list:
        if time.perf_counter() > deadline:
            raise TimeoutExceededError("fuzzy label matching timed out")

        c_norm = _normalize_for_match(c)
        c_tokens = set(c_norm.split())
        if not q_tokens or not c_tokens:
            score = 0.0
        else:
            intersection = len(q_tokens & c_tokens)
            union = len(q_tokens | c_tokens)
            score = intersection / union
        if score >= threshold:
            scored.append((c, float(score)))

    # No timeout – mirror behaviour of non-timed version
    scored.sort(key=lambda t: t[1], reverse=True)

    if limit is not None and isinstance(limit, int) and limit > 0:
        scored = scored[:limit]

    if include_scores:
        return scored
    return [label for (label, _score) in scored]
