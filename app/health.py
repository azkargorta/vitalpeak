from __future__ import annotations
from typing import Dict, List
from .datastore import load_user, save_user


def add_weight(username: str, date_iso: str, weight: float) -> None:
    data = load_user(username)
    data.setdefault("weights", []).append({"date": date_iso, "weight": float(weight)})
    save_user(username, data)


def list_weights(username: str) -> List[Dict]:
    data = load_user(username)
    return data.get("weights", [])


def delete_weights(username: str, indices: List[int]) -> int:
    """Delete weight entries by their *original* index in the stored list.

    Args:
        username: user identifier
        indices: list indices to delete (0-based), as stored in the JSON list

    Returns:
        Number of deleted entries.
    """
    data = load_user(username) or {}
    weights = data.get("weights", [])
    if not weights or not indices:
        return 0

    idx_set = {int(i) for i in indices if i is not None}
    new_weights = [w for j, w in enumerate(weights) if j not in idx_set]
    removed = len(weights) - len(new_weights)
    data["weights"] = new_weights
    save_user(username, data)
    return removed
