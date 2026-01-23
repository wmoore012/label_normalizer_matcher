# Label Normalizer Matcher

[![CI](https://github.com/wmoore012/label_normalizer_matcher/actions/workflows/ci.yml/badge.svg)](https://github.com/wmoore012/label_normalizer_matcher/actions/workflows/ci.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/wmoore012/label_normalizer_matcher/blob/main/LICENSE)

> **Built for [Perday CatalogLAB](https://perdaycatalog.com)** - a data story platform for music producers and songwriters.
>
> [![CatalogLAB Data Story](docs/data_story.png)](https://perdaycatalog.com)

Music label normalization and entity matching for catalog analytics.

**Repo:** https://github.com/wmoore012/label_normalizer_matcher
**What it does:** Resolves "Atlantic Records" vs "Atlantic Recording Corporation" vs "ATLANTIC RECORDS LLC" into a single canonical entity so analytics don't double-count.

## Why I Built It

Every data source spells labels differently:
- Spotify says "Atlantic Records"
- Apple Music says "Atlantic Recording Corporation"
- YouTube says "ATLANTIC"
- Your distributor says "atlantic records, llc."

Without normalization, your analytics show 4 different labels instead of 1. Aggregations break. Reports lie.

I built `label_normalizer_matcher` to create a canonical label graph for CatalogLAB. It uses fuzzy matching, acronym expansion, and suffix stripping to match labels correctly.

## Key Features

- **Fuzzy matching** with tunable similarity thresholds
- **Legal suffix stripping**: LLC, Inc., Ltd., Corp., GmbH, etc.
- **Acronym handling**: UMG = Universal Music Group
- **Parent/subsidiary relationships** for major label hierarchies
- **Confidence scoring** for match quality

## Installation

```bash
pip install label-normalizer-matcher
```

Or clone locally:

```bash
git clone https://github.com/wmoore012/label_normalizer_matcher.git
cd label_normalizer_matcher
pip install -e .
```

## Quick Start

```python
from label_normalizer_matcher import LabelMatcher

matcher = LabelMatcher()

# These all match to the same canonical label
matcher.normalize("Atlantic Records")           # -> "Atlantic Records"
matcher.normalize("Atlantic Recording Corp")    # -> "Atlantic Records"
matcher.normalize("ATLANTIC RECORDS LLC")       # -> "Atlantic Records"

# Check if two labels are the same entity
match = matcher.match("Def Jam", "Def Jam Recordings")
print(match.is_match)       # True
print(match.confidence)     # 0.95
```

## Performance

| Metric | Value |
|--------|-------|
| Normalization | 50K labels/sec |
| Matching | 10K comparisons/sec |
| Accuracy | 97% on major label datasets |

See [BENCHMARKS.md](BENCHMARKS.md) for detailed results.

## Documentation

- [API Documentation](docs/)
- [Examples](examples/)
- [Contributing Guide](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)

## Professional Context

Built by **Wilton Moore** for Perday Labs. The music industry has thousands of labels, imprints, and subsidiaries. This module makes it possible to aggregate data correctly across the entire ecosystem.

## Contact

Questions about music metadata or collabs?
- LinkedIn: https://www.linkedin.com/in/wiltonmoore/
- GitHub: https://github.com/wmoore012

## License

MIT License. See [LICENSE](LICENSE) for details.
