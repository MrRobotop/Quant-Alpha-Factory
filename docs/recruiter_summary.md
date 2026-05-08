# Recruiter Summary

Quant Alpha Factory is a production-style quant research platform by Rishabh Patil, built around
Microsoft Qlib and Microsoft RD-Agent integration points.

## What It Shows

- Typed, modular Python package structure.
- Deterministic CLI workflows with Typer.
- Synthetic-data tests that do not require secrets or internet access.
- Qlib conversion and qrun wrappers with dry-run safety.
- Real Qlib synthetic demo execution with Qlib/MLflow metric parsing.
- Controlled RD-Agent execution wrappers with human hypothesis review.
- Experiment manifests for config/data/code hashes, costs, metrics, artifacts, status, and failures.
- Research validity checks for date splits, leakage patterns, fit/test overlap, and transaction
  cost assumptions.
- Versioned factor metadata with economic rationale and leakage notes.
- Cost-aware portfolio metrics, turnover reporting, drawdown, benchmark metadata, and tearsheets.
- Read-only API/dashboard helpers over stored artifacts.
- Docker, Compose, and GitHub Actions CI.

## Claim Discipline

This repository does not claim live tradable performance. The included demo is synthetic and exists
to prove the workflow: validate data, construct Qlib/RD-Agent dry-run commands, run research checks,
write a manifest, update the leaderboard, and generate a report.

## Why It Matters

The project emphasizes the infrastructure concerns that make quant research credible:

- Reproducibility before experimentation.
- Data validation before modeling.
- Leakage checks before comparison.
- Cost-adjusted metrics before strategy ranking.
- Human review before promoting agent-generated ideas.
- Artifact-backed reports instead of fabricated performance claims.

## Best Review Path

```bash
make install
make quickstart
python -m src.cli experiments leaderboard --metric net_return
python -m src.cli report build --experiment-id synthetic-demo
```

The demo produces synthetic artifacts under `artifacts/experiments` and `artifacts/reports`.

For live integration setup, see `docs/real_execution.md`.
For a guided review, see `docs/project_walkthrough.md`.
