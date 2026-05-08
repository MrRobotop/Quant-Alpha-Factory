# Limitations And Next Steps

## Current Limitations

- Bundled results use deterministic synthetic data and are not investment performance claims.
- No licensed market dataset is included.
- Real RD-Agent workflows require user-provided LLM credentials.
- RD-Agent package and Docker readiness can be checked without keys, but agent generation remains
  opt-in.
- Qlib execution has been validated locally on synthetic data, not on a production market dataset.
- Qlib/MLflow artifact parsing is conservative and should be expanded as more recorder outputs are
  observed.
- The dashboard is intentionally minimal and reads stored artifacts only.
- The transaction cost model is simple and linear.
- Sector neutrality, volatility targeting, richer slippage, and borrow/shorting assumptions remain
  future work.

## Next Steps

- Add a report profile specifically for Qlib demo manifests.
- Add a credentialed RD-Agent smoke target that remains excluded from CI.
- Add richer strategy wrappers for sector-neutral, volatility-scaled, and Top-K Dropout variants.
- Add a persistent experiment backend such as SQLite or PostgreSQL if filesystem storage becomes
  limiting.
- Add dashboard screenshots generated from synthetic artifacts.
- Validate the workflow on licensed market data and document all data assumptions.

See `docs/real_execution.md` for the user-facing setup path for real Qlib and RD-Agent runs.
