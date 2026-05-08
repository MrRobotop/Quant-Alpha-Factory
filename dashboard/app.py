"""Optional Streamlit dashboard entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from api.main import leaderboard_payload, list_experiments_payload


def dashboard_status() -> str:
    """Return dashboard scaffold status without requiring Streamlit."""
    return "dashboard scaffold"


def load_dashboard_data(store_root: str | Path = "artifacts/experiments") -> dict[str, Any]:
    """Load read-only dashboard data from stored experiment manifests."""
    return {
        "experiments": list_experiments_payload(store_root),
        "leaderboard": leaderboard_payload(store_root),
    }


def main() -> None:
    """Run the optional Streamlit dashboard."""
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError(
            "Streamlit is optional. Install with `pip install -e '.[dashboard]'`."
        ) from exc

    st.set_page_config(page_title="Quant Alpha Factory", layout="wide")
    st.title("Quant Alpha Factory")
    data = load_dashboard_data()

    st.subheader("Leaderboard")
    if data["leaderboard"]:
        st.dataframe(data["leaderboard"], use_container_width=True)
    else:
        st.info("No experiments found.")

    st.subheader("Experiments")
    if data["experiments"]:
        st.dataframe(data["experiments"], use_container_width=True)
    else:
        st.info("No stored experiment manifests available.")


if __name__ == "__main__":
    main()
