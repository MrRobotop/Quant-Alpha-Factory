# Architecture

Quant Alpha Factory is organized around explicit boundaries:

- `src.data`: ingestion, canonical OHLCV schema, validation, and validated Qlib conversion command
  construction.
- `src.qlib_integration`: Qlib config loading, dry-run support, subprocess execution, stdout/stderr
  log capture, and conservative result parsing.
- `src.rd_agent_adapter`: safe RD-Agent command construction, dry-run/execute management, log
  parsing, manifest recording, and human hypothesis review.
- `src.experiments`: JSON manifests, artifact storage, lineage hashes, failed-run recording, and
  leaderboard queries.
- `src.validation`: leakage checks, date split checks, and research validity reports.
- `src.factors`: versioned factor metadata, registry, baseline Qlib expression factor library, and
  IC/rank IC evaluation helpers.
- `src.strategies` and `src.backtest`: strategy interfaces, Top-K weights, turnover constraints,
  transaction cost adjustment, cost-aware metrics, and Markdown tearsheets.
- `src.reporting`: Markdown research reports and optional plotting helpers from stored artifacts.
- `api` and `dashboard`: optional read-only interfaces over stored experiment artifacts and
  leaderboard rows.
- `src.demo`: deterministic synthetic workflows that exercise the platform without live data,
  Qlib execution, RD-Agent execution, or credentials.

Qlib and RD-Agent are integration targets, not hidden global dependencies. Tests and CI exercise
command construction, validation, manifests, and dry-run paths without requiring live data or
credentials. Real conversion or agent execution must be explicitly requested.

See `docs/limitations.md` for known boundaries and planned extensions.
See `docs/real_execution.md` for live Qlib/RD-Agent setup.
