"""Optional plotting helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def plotting_available() -> bool:
    """Return whether optional plotting dependencies are available."""
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        return False
    return True


def save_equity_curve_plot(equity_curve: pd.Series, output_path: str | Path) -> Path:
    """Save an equity curve plot when matplotlib is installed."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Plotting requires optional dependency matplotlib.") from exc

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots()
    equity_curve.plot(ax=axis)
    axis.set_title("Equity Curve")
    axis.set_xlabel("Date")
    axis.set_ylabel("Equity")
    figure.tight_layout()
    figure.savefig(path)
    plt.close(figure)
    return path

