# Research Methodology

The research workflow is designed to protect against common quant research errors:

- Data must pass schema and quality validation before conversion or modeling.
- Qlib conversion must be blocked when validation has errors.
- Train, validation, and test periods must be explicit and non-overlapping.
- Feature processors must not be fitted on validation or test data unless explicitly justified.
- Every experiment must record data source, config, code hash when available, seed, universe,
  benchmark, transaction cost assumptions, metrics, artifacts, and failure status.
- Failed experiments must be recorded with a failure reason so research gaps and operational
  failures remain auditable.
- Qlib artifacts must be parsed from files produced by actual runs. Missing artifacts must be
  reported as unavailable, not inferred.
- Strategy comparison must include transaction-cost-adjusted results and turnover.
- Strategy ranking must not rely on gross return alone; net return, turnover, drawdown, costs, and
  benchmark-relative behavior must be reported together.
- Synthetic data may be used for tests and demos, but synthetic results must not be presented as
  live tradable performance.
- Every factor must include required inputs, implementation type, economic rationale, leakage notes,
  and version before it can be evaluated or promoted.
- Research checks must pass before comparing results or promoting generated factors/models.
- RD-Agent generated hypotheses require human review before promotion into the factor/model library.
- Reports must be generated from stored artifacts and must mark missing metrics as unavailable.
- API and dashboard views must read stored artifacts by default instead of recomputing experiments.
- Synthetic demo metrics are useful for software validation only and must not be presented as real
  market performance.

The initial baseline should be simple and reproducible before agentic factor/model generation is
enabled.

The repository is intentionally conservative: absence of artifacts is reported as unavailable, not
estimated, and synthetic metrics are treated as software-validation outputs only.
