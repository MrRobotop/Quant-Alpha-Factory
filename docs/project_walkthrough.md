# Project Walkthrough

This walkthrough is the recommended path for reviewing Quant Alpha Factory as a portfolio project.
It uses synthetic data and does not require live market data or LLM credentials.

## 1. Install And Validate

```bash
python -m venv .venv
source .venv/bin/activate
make install
make quickstart
```

This runs the no-secret validation path: lint, tests, CLI status, data validation, research checks,
Qlib dry-run, RD-Agent dry-run, and the synthetic end-to-end demo.

## 2. Inspect The Data Layer

Key files:

```text
src/data/schema.py
src/data/ingestion.py
src/data/validation.py
src/data/qlib_converter.py
tests/data/
```

The data layer rejects duplicate `(date, symbol)` keys, invalid OHLC relationships, bad date order,
negative prices, negative volume, and suspicious adjusted-close behavior.

## 3. Inspect Research Controls

Key files:

```text
src/validation/splits.py
src/validation/leakage.py
src/validation/research_checks.py
docs/leakage_policy.md
```

The research checks are intentionally conservative. They flag bad date splits, fit periods that
overlap test periods, suspicious future references, label leakage patterns, and missing transaction
cost assumptions.

## 4. Run The Synthetic Demo

```bash
python -m src.cli demo synthetic
python -m src.cli experiments leaderboard --metric net_return
python -m src.cli report build --experiment-id synthetic-demo
```

The synthetic demo records a manifest and report, then exposes them through the experiment store.
Metrics are synthetic and should be read as workflow checks only.

## 5. Review Qlib Integration

Dry-run:

```bash
python -m src.cli qlib demo --dry-run
```

Real synthetic Qlib execution:

```bash
make install-real
make qlib-demo-real
```

The real Qlib demo validates data, writes Qlib-compatible storage, runs `qrun`, parses Qlib/MLflow
metrics, and writes a project manifest.

## 6. Review RD-Agent Controls

No-key readiness:

```bash
DS_CODER_COSTEER_ENV_TYPE=docker \
  python -m src.cli doctor --component rdagent --allow-missing-llm --strict
```

Dry-run command construction:

```bash
python -m src.cli rdagent health --dry-run
python -m src.cli rdagent run --mode fin_factor --loop-n 1 --dry-run
```

Real RD-Agent workflows require user-provided LLM credentials and remain explicit opt-in.

## 7. What To Look For In Code Review

- Clear module boundaries and small interfaces.
- Explicit config, data, and artifact paths.
- Failed-run manifest recording.
- No fabricated metrics.
- Cost-aware metrics and turnover reporting.
- Human review before promoting agent-generated hypotheses.
- CI paths that do not require secrets.

## 8. Interview Talking Points

- Why Qlib and RD-Agent are wrapped rather than called ad hoc.
- How manifests make research auditable.
- How leakage checks reduce false confidence.
- Why synthetic demos are useful but cannot support performance claims.
- How the platform can be extended with licensed market data, richer strategies, and persistent
  experiment storage.
