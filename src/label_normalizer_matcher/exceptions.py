# SPDX - License - Identifier: MIT
# Copyright (c) 2025 Perday CatalogLAB™

"""Exception classes for Label Normalizer Matcher.

These exceptions are intentionally small and well-typed so that downstream
code (and tests) can reason about specific failure modes without depending
on the full implementation details of the matcher.
"""

from __future__ import annotations

from typing import Any


class LabelNormalizationError(Exception):
    """Raised when label normalization fails for a specific input."""


class ValidationError(Exception):
    """Structured validation error used by :mod:`validation` helpers.

    Parameters are intentionally explicit so error messages can be rendered in
    logs, APIs or CLI tools without additional context.
    """

    def __init__(
        self,
        field_name: str,
        value: Any,
        expected: str,
        suggestion: str | None = None,
    ) -> None:
        self.field_name = field_name
        self.value = value
        self.expected = expected
        self.suggestion = suggestion

        message = (
            f"Validation failed for field '{field_name}': expected {expected!s}, "
            f"got {value!r}."
        )
        if suggestion:
            message = f"{message} Suggestion: {suggestion}"
        super().__init__(message)


class MissingExtraError(ImportError):
    """Raised when an optional dependency is required but not installed."""


class TimeoutExceededError(TimeoutError, LabelNormalizationError):
    """Raised when an operation exceeds its allotted time budget."""
