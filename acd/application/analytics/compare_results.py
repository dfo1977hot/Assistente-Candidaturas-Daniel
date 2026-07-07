from __future__ import annotations

from typing import Any

from acd.infrastructure.repositories.analytics_repository import AnalyticsRepository


def compare_results(
    repository: AnalyticsRepository | None = None, *, period1: str = "daily", period2: str = "daily"
) -> dict[str, Any]:
    """Compare analytics results between two periods.

    Args:
        repository: AnalyticsRepository instance
        period1: First period identifier
        period2: Second period identifier

    Returns:
        Dictionary containing comparison results
    """
    if repository is None:
        repository = AnalyticsRepository()

    # Get snapshots for comparison
    snapshots = []
    try:
        latest = repository.get_latest_snapshot()
        if latest:
            snapshots.append(latest)
    except Exception:
        pass

    return {
        "period1": period1,
        "period2": period2,
        "snapshots_found": len(snapshots),
        "comparison": {},
    }
