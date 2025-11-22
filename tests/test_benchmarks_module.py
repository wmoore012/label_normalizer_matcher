# SPDX - License - Identifier: MIT
# Copyright (c) 2025 Perday CatalogLAB™

"""
Tests for the benchmarks module functionality.
"""

from label_normalizer_matcher.benchmarks import (
    BenchmarkResult,
    LabelNormalizerBenchmark,
    generate_realistic_labels,
)


class TestBenchmarkModule:
    """Test the benchmarking module."""

    def test_generate_realistic_labels(self):
        """Test realistic label generation."""
        labels = generate_realistic_labels(50)

        assert len(labels) == 50
        assert all(isinstance(label, str) for label in labels)
        assert all(len(label) > 0 for label in labels)

        # Should have some variety
        unique_labels = set(labels)
        assert len(unique_labels) > 10  # Should have variety

    def test_benchmark_result_dataclass(self):
        """Test BenchmarkResult dataclass."""
        result = BenchmarkResult(
            operation="test_op",
            labels_processed=100,
            duration_seconds=0.5,
            labels_per_second=200.0,
            memory_usage_mb=10.0,
            cache_hit_rate=0.8,
            timestamp="2025 - 01 - 01T00:00:00",
        )

        assert result.operation == "test_op"
        assert result.labels_processed == 100
        assert result.duration_seconds == 0.5
        assert result.labels_per_second == 200.0
        assert result.memory_usage_mb == 10.0
        assert result.cache_hit_rate == 0.8
        assert result.timestamp == "2025 - 01 - 01T00:00:00"

    def test_benchmark_runner_init(self):
        """Test benchmark runner initialization."""
        benchmark = LabelNormalizerBenchmark()

        assert benchmark.results == []

    def test_benchmark_normalization(self):
        """Test normalization benchmarking."""
        benchmark = LabelNormalizerBenchmark()
        labels = generate_realistic_labels(10)

        result = benchmark.benchmark_normalization(labels)

        assert isinstance(result, BenchmarkResult)
        assert result.operation == "normalize_label"
        assert result.labels_processed == 10
        assert result.duration_seconds >= 0
        assert result.labels_per_second > 0
        assert result.memory_usage_mb >= 0
        assert 0 <= result.cache_hit_rate <= 1
        assert len(benchmark.results) == 1

    def test_benchmark_canonical_ids(self):
        """Test canonical ID benchmarking."""
        benchmark = LabelNormalizerBenchmark()
        labels = generate_realistic_labels(10)

        result = benchmark.benchmark_canonical_ids(labels)

        assert isinstance(result, BenchmarkResult)
        assert result.operation == "get_canonical_label_id"
        assert result.labels_processed == 10
        assert result.duration_seconds >= 0
        assert result.labels_per_second > 0
        assert result.memory_usage_mb >= 0
        assert 0 <= result.cache_hit_rate <= 1
        assert len(benchmark.results) == 1

    def test_benchmark_copyright_stripping(self):
        """Test copyright stripping benchmarking."""
        benchmark = LabelNormalizerBenchmark()
        labels = [
            "℗ 2023 Sony Music Entertainment, Inc.",
            "(P) 2022 Warner Music Group Corp.",
            "2021 Universal Music Group LLC",
        ]

        result = benchmark.benchmark_copyright_stripping(labels)

        assert isinstance(result, BenchmarkResult)
        assert result.operation == "strip_year_and_suffix"
        assert result.labels_processed == 3
        assert result.duration_seconds >= 0
        assert result.labels_per_second > 0
        assert result.memory_usage_mb >= 0
        assert result.cache_hit_rate == 0.0  # No caching for this operation
        assert len(benchmark.results) == 1

    def test_comprehensive_benchmark(self):
        """Test comprehensive benchmarking."""
        benchmark = LabelNormalizerBenchmark()

        results = benchmark.run_comprehensive_benchmark(sample_size=20)

        assert isinstance(results, dict)
        assert "normalization" in results
        assert "canonical_ids" in results
        assert "copyright_stripping" in results

        # Should have 3 results stored
        assert len(benchmark.results) == 3

        # Each result should be valid
        for result in benchmark.results:
            assert isinstance(result, BenchmarkResult)
            assert result.labels_processed > 0
            assert result.duration_seconds >= 0
            assert result.labels_per_second > 0

    def test_save_and_print_results(self, tmp_path):
        """Test saving and printing results."""
        benchmark = LabelNormalizerBenchmark()
        labels = generate_realistic_labels(5)

        # Generate some results
        benchmark.benchmark_normalization(labels)
        benchmark.benchmark_canonical_ids(labels)

        # Test saving
        output_file = tmp_path / "test_results.json"
        benchmark.save_results(str(output_file))

        assert output_file.exists()

        # Test file content
        import json

        with open(output_file) as f:
            data = json.load(f)

        assert "benchmark_run" in data
        assert "results" in data
        assert len(data["results"]) == 2

        # Test printing (should not raise exceptions)
        benchmark.print_summary()

    def test_print_summary_empty(self, capsys):
        """Test printing summary with no results."""
        benchmark = LabelNormalizerBenchmark()
        benchmark.print_summary()

        captured = capsys.readouterr()
        assert "No benchmark results available" in captured.out
