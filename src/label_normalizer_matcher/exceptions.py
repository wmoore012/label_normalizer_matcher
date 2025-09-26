# SPDX-License-Identifier: MIT
# Copyright (c) 2024 MusicScope

"""Exception classes for Label Normalizer Matcher."""

from __future__ import annotations


class LabelNormalizationError(Exception):
    """Raised when label normalization fails for a specific input."""


class MissingExtraError(ImportError):
    """Raised when an optional dependency is required but not installed."""


class TimeoutExceededError(TimeoutError):
    """Raised when an operation exceeds its allotted time budget."""
