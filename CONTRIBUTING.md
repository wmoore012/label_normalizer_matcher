<!-- SPDX-License-Identifier: MIT
Copyright (c) 2025 Perday Labs -->

# Contributing to Label Normalizer Matcher

We welcome contributions! This guide will help you get started.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/music-data-oss/label-normalizer-matcher.git
cd label-normalizer-matcher
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev,benchmark]"
```

## Running Tests

Run the full test suite:
```bash
pytest
```

Run specific test categories:
```bash
# Unit tests only
pytest tests/test_core.py

# Integration tests (requires database)
pytest tests/test_integration.py

# Benchmark tests
pytest tests/test_benchmarks.py -m benchmark
```

## Code Quality

We maintain high code quality standards:

### Linting and Formatting
```bash
# Check code style
ruff check src tests

# Format code
ruff format src tests

# Type checking
mypy src/label_normalizer_matcher
```

### Test Coverage
Maintain >90% test coverage:
```bash
pytest --cov=label_normalizer_matcher --cov-report=html
```

### Security Scanning
```bash
bandit -r src/
```

## Performance Requirements

New features must meet performance standards:
- Normalization: >2,000 labels/second
- ID generation: >1,000 IDs/second
- Cache hit rate: >80% with realistic duplicate patterns
- Memory usage: <200MB for large datasets

Run benchmarks to verify:
```bash
pytest tests/test_benchmarks.py -m benchmark -v
```

## Adding New Features

1. **Write tests first** (TDD approach)
2. **Use real music industry data** in tests when possible
3. **Maintain backward compatibility**
4. **Update documentation** and examples
5. **Add benchmark tests** for performance-critical features

## Testing with Real Data

We prefer tests using real music industry data over synthetic data:

```python
# Good - uses realistic label patterns
def test_major_labels():
    assert normalize_label("Sony Music Entertainment, Inc.") == "Sony Music Entertainment"
    assert normalize_label("Warner Music Group Corp.") == "Warner Music Group"

# Avoid - synthetic test data
def test_generic_labels():
    assert normalize_label("Test Label, Inc.") == "Test Label"
```

## Submitting Changes

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Make your changes** following the guidelines above
4. **Run all tests**: `pytest`
5. **Run quality checks**: `ruff check src tests && mypy src/label_normalizer_matcher`
6. **Commit with clear messages**: `git commit -m "Add feature: description"`
7. **Push to your fork**: `git push origin feature-name`
8. **Create a Pull Request**

## Pull Request Guidelines

- **Clear description** of what the PR does
- **Reference any related issues**
- **Include tests** for new functionality
- **Update documentation** if needed
- **Ensure CI passes** (all tests, linting, type checking)
- **Add benchmark results** for performance changes

## Code Style

- Follow PEP 8 (enforced by ruff)
- Use type hints for all public APIs
- Write clear docstrings with examples
- Keep functions focused and testable
- Use descriptive variable names

## Documentation

- Update README.md for new features
- Add docstring examples that work
- Update CHANGELOG.md for releases
- Include performance characteristics

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for design questions
- Check existing issues before creating new ones

Thank you for contributing to making music data processing better!
