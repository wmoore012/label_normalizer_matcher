<!-- SPDX-License-Identifier: MIT
Copyright (c) 2024 MusicScope -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-12-17

### Added
- Initial release of label-normalizer-matcher
- Core label normalization functionality with corporate suffix removal
- Copyright year and symbol stripping for music metadata
- Stable canonical ID generation with MD5 hashing
- High-performance caching system
- Comprehensive test suite with real-world music industry patterns
- Benchmark tests demonstrating >2000 labels/second performance
- Full type hints and mypy compliance
- CI/CD pipeline with automated testing and security scanning

### Features
- `normalize_label()` - Clean label names by removing corporate suffixes
- `get_canonical_label_id()` - Generate stable IDs for database foreign keys
- `strip_year_and_suffix()` - Handle copyright metadata from music platforms
- `clear_cache()` - Cache management for testing and memory control
- `get_cache_stats()` - Performance monitoring and cache effectiveness

### Performance
- Normalization speed: >2,000 labels/second
- Cache hit rate: >90% for repeated lookups
- Memory efficient: <200MB for 100K+ unique labels
- ID stability: 100% consistent across application restarts
