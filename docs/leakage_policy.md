# Leakage Policy

No result is considered valid unless leakage checks pass or documented exceptions are reviewed.

The platform must reject or flag:

- Overlapping train, validation, and test windows.
- Features that directly reference labels or future returns.
- Qlib processors fitted on test-period data.
- Forward-filled labels.
- Duplicate `(date, symbol)` rows.
- Benchmark or universe changes during uncontrolled model comparison.

Qlib label definitions are allowed only when they are isolated from features and recorded in the
experiment configuration. RD-Agent generated factors require human review before promotion.

Implemented checks currently inspect Qlib-style train/validation/test segments, handler fit periods,
feature/factor/expression fields, and transaction cost declarations. These checks are conservative
guards, not a formal proof of no leakage.

RD-Agent output is treated as untrusted research input. Generated factors or models require human
review and must pass research checks before promotion.
