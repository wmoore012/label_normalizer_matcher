# Label Database Refresh & Versioning

This project never stores raw label data in git. Instead, we point at the
production tables documented below and keep a changelog entry each time the
dataset is refreshed.

## Source of Truth

- **Database**: `icatalog_public`
- **Tables**: `labels` (canonical rows), `label_aliases` (variant → canonical)
- Schema access pattern matches the queries in
  `tests/test_label_integration.py`.

## Refresh Workflow

1. Export a sanitized snapshot (only `label_id`, `label_name`, `updated_at`):

   ```sql
   SELECT label_id, label_name, updated_at
   FROM labels
   WHERE label_name IS NOT NULL AND label_name != ''
   ORDER BY label_id;
   ```

   Keep the CSV/JSON export outside this repo (private storage or S3).

2. Record the snapshot name (e.g. `label_snapshot_2025-02-10.csv`) in
   `CHANGELOG.md` under a new heading (`## Label DB v2025.02`).

3. Update any private benchmark fixtures to point at the new snapshot.

4. Run:

   ```bash
   pytest tests/test_label_integration.py -k normalize
   pytest tests/test_label_benchmarks.py
   ```

   This validates both normalization rules and throughput with the refreshed
   data.

5. When publishing benchmark numbers, reference the snapshot version, e.g.
   “Benchmarked with `label_snapshot_2025-02-10`”.

## Versioning & Rollback

- `CHANGELOG.md` tracks every dataset version plus the normalization changes
  that accompanied it. Link benchmark runs to the same entry so it’s clear
  which label set produced which metrics.
- Keep the last two snapshots in your secure storage so you can roll back by
  pointing the ETL job at the previous file and noting the reversion in the
  changelog.

## Sanitization Rules

- Do **not** commit the raw CSV/JSON export.
- Remove any internal notes/owner metadata columns before saving a snapshot.
- If you need to debug a specific label, use temporary exports and delete them
  after the fix is merged.
