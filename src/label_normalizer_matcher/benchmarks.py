# SPDX - License - Identifier: MIT
# Copyright (c) 2025 Perday CatalogLAB™

"""
Benchmarking utilities for label normalization performance.

This module provides tools to measure and track performance metrics
for the label normalization functions.
"""

import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from .core import (
    clear_cache,
    get_canonical_label_id,
    normalize_label,
    strip_year_and_suffix,
)


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""

    operation: str
    labels_processed: int
    duration_seconds: float
    labels_per_second: float
    memory_usage_mb: float
    cache_hit_rate: float
    timestamp: str


class LabelNormalizerBenchmark:
    """Benchmark runner for label normalization operations."""

    def __init__(self):
        self.results: List[BenchmarkResult] = []

    def benchmark_normalization(
        self, labels: List[str], clear_cache_first: bool = True
    ) -> BenchmarkResult:
        """
        Benchmark label normalization performance.

        Args:
            labels: List of label names to normalize
            clear_cache_first: Whether to clear cache before benchmarking

        Returns:
            BenchmarkResult with performance metrics
        """
        if clear_cache_first:
            clear_cache()

        # Get initial memory usage
        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            initial_memory = 0.0

        # Run benchmark
        start_time = time.time()

        for label in labels:
            normalize_label(label)

        duration = time.time() - start_time

        # Get final memory usage
        try:
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = final_memory - initial_memory
        except (ImportError, NameError):
            memory_usage = 0.0

        # Get cache stats
        from .core import get_cache_stats

        stats = get_cache_stats()

        # Calculate metrics
        labels_per_second = len(labels) / duration if duration > 0 else float("inf")

        result = BenchmarkResult(
            operation="normalize_label",
            labels_processed=len(labels),
            duration_seconds=duration,
            labels_per_second=labels_per_second,
            memory_usage_mb=memory_usage,
            cache_hit_rate=stats.hit_rate,
            timestamp=datetime.now().isoformat(),
        )

        self.results.append(result)
        return result

    def benchmark_canonical_ids(
        self, labels: List[str], clear_cache_first: bool = True
    ) -> BenchmarkResult:
        """
        Benchmark canonical ID generation performance.

        Args:
            labels: List of label names to generate IDs for
            clear_cache_first: Whether to clear cache before benchmarking

        Returns:
            BenchmarkResult with performance metrics
        """
        if clear_cache_first:
            clear_cache()

        # Get initial memory usage
        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            initial_memory = 0.0

        # Run benchmark
        start_time = time.time()

        for label in labels:
            get_canonical_label_id(label)

        duration = time.time() - start_time

        # Get final memory usage
        try:
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = final_memory - initial_memory
        except (ImportError, NameError):
            memory_usage = 0.0

        # Get cache stats
        from .core import get_cache_stats

        stats = get_cache_stats()

        # Calculate metrics
        labels_per_second = len(labels) / duration if duration > 0 else float("inf")

        result = BenchmarkResult(
            operation="get_canonical_label_id",
            labels_processed=len(labels),
            duration_seconds=duration,
            labels_per_second=labels_per_second,
            memory_usage_mb=memory_usage,
            cache_hit_rate=stats.hit_rate,
            timestamp=datetime.now().isoformat(),
        )

        self.results.append(result)
        return result

    def benchmark_copyright_stripping(self, labels: List[str]) -> BenchmarkResult:
        """
        Benchmark copyright stripping performance.

        Args:
            labels: List of labels with copyright info to strip

        Returns:
            BenchmarkResult with performance metrics
        """
        # Get initial memory usage
        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            initial_memory = 0.0

        # Run benchmark
        start_time = time.time()

        for label in labels:
            strip_year_and_suffix(label)

        duration = time.time() - start_time

        # Get final memory usage
        try:
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = final_memory - initial_memory
        except (ImportError, NameError):
            memory_usage = 0.0

        # Calculate metrics
        labels_per_second = len(labels) / duration if duration > 0 else float("inf")

        result = BenchmarkResult(
            operation="strip_year_and_suffix",
            labels_processed=len(labels),
            duration_seconds=duration,
            labels_per_second=labels_per_second,
            memory_usage_mb=memory_usage,
            cache_hit_rate=0.0,  # No caching for this operation
            timestamp=datetime.now().isoformat(),
        )

        self.results.append(result)
        return result

    def run_comprehensive_benchmark(
        self, sample_size: int = 1000
    ) -> Dict[str, BenchmarkResult]:
        """
        Run comprehensive benchmarks on all operations.

        Args:
            sample_size: Number of labels to test with

        Returns:
            Dictionary of operation names to benchmark results
        """
        # Generate realistic test data
        base_labels = [
            "Sony Music Entertainment, Inc.",
            "Warner Music Group Corp.",
            "Universal Music Group LLC",
            "Atlantic Records Ltd.",
            "Columbia Records",
            "Def Jam Recordings",
            "Interscope Records",
            "Capitol Records LLC",
            "RCA Records, Inc.",
            "Epic Records Corp.",
        ]

        copyright_labels = [
            "℗ 2023 Sony Music Entertainment, Inc.",
            "(P) 2022 Warner Music Group Corp.",
            "2021 Universal Music Group LLC",
            "℗ 2020 Atlantic Records Ltd.",
            "(P) 2019 Columbia Records, Inc.",
        ]

        # Create test datasets
        normalization_labels = (base_labels * (sample_size // len(base_labels) + 1))[
            :sample_size
        ]
        copyright_test_labels = (
            copyright_labels * (sample_size // len(copyright_labels) + 1)
        )[:sample_size]

        results = {}

        # Benchmark normalization
        results["normalization"] = self.benchmark_normalization(normalization_labels)

        # Benchmark canonical ID generation
        results["canonical_ids"] = self.benchmark_canonical_ids(normalization_labels)

        # Benchmark copyright stripping
        results["copyright_stripping"] = self.benchmark_copyright_stripping(
            copyright_test_labels
        )

        return results

    def save_results(self, filename: str) -> None:
        """Save benchmark results to JSON file."""
        data = {
            "benchmark_run": datetime.now().isoformat(),
            "results": [
                {
                    "operation": r.operation,
                    "labels_processed": r.labels_processed,
                    "duration_seconds": r.duration_seconds,
                    "labels_per_second": r.labels_per_second,
                    "memory_usage_mb": r.memory_usage_mb,
                    "cache_hit_rate": r.cache_hit_rate,
                    "timestamp": r.timestamp,
                }
                for r in self.results
            ],
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

    def print_summary(self) -> None:
        """Print a summary of benchmark results."""
        if not self.results:
            print("No benchmark results available.")
            return

        print("\n" + "=" * 60)
        print("LABEL NORMALIZER BENCHMARK RESULTS")
        print("=" * 60)

        for result in self.results:
            print(f"\nOperation: {result.operation}")
            print(f"  Labels processed: {result.labels_processed:,}")
            print(f"  Duration: {result.duration_seconds:.3f}s")
            print(f"  Performance: {result.labels_per_second:,.0f} labels / second")
            print(f"  Memory usage: {result.memory_usage_mb:.1f} MB")
            if result.cache_hit_rate > 0:
                print(f"  Cache hit rate: {result.cache_hit_rate:.1%}")

        print("\n" + "=" * 60)


def generate_realistic_labels(count: int) -> List[str]:
    """
    Generate realistic music industry label names for testing.

    Args:
        count: Number of labels to generate

    Returns:
        List of realistic label names
    """
    patterns = [
        "Sony Music Entertainment, Inc.",
        "Warner Music Group Corp.",
        "Universal Music Group LLC",
        "Atlantic Records Ltd.",
        "Columbia Records",
        "Def Jam Recordings",
        "Interscope Records",
        "Capitol Records LLC",
        "RCA Records, Inc.",
        "Epic Records Corp.",
        "℗ 2023 Sony Music Entertainment, Inc.",
        "(P) 2022 Warner Music Group Corp.",
        "2021 Universal Music Group LLC",
        "EMI Records Ltd.",
        "Parlophone Records Ltd.",
        "Domino Recording Co Ltd.",
        "XL Recordings Ltd.",
        "Rough Trade Records",
        "Sub Pop Records, Inc.",
        "Matador Records LLC",
    ]

    labels = []
    for i in range(count):
        base = patterns[i % len(patterns)]
        # Add variations
        if i % 4 == 0:
            labels.append(f"  {base}  ")  # Whitespace
        elif i % 4 == 1:
            labels.append(base.upper())  # Uppercase
        elif i % 4 == 2:
            labels.append(base.lower())  # Lowercase
        else:
            labels.append(base)  # Original

    return labels


if __name__ == "__main__":
    # Run benchmarks when called directly
    benchmark = LabelNormalizerBenchmark()
    results = benchmark.run_comprehensive_benchmark(sample_size=5000)
    benchmark.print_summary()
    benchmark.save_results("benchmark_results.json")
