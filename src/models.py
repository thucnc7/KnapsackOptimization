"""Core data models for knapsack benchmark instances."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Union


@dataclass(frozen=True)
class Item:
    """Single knapsack item with weight and value."""
    id: int
    w: int
    v: int


@dataclass(frozen=True)
class KnapsackInstance:
    """Problem instance with metadata and a list of items."""
    test_id: str
    metadata: Dict[str, Union[int, float]]
    items: List[Item]

    def to_json_dict(self) -> Dict[str, object]:
        """Serialize the instance to a JSON-ready dictionary."""
        return {
            "test_id": self.test_id,
            "metadata": self.metadata,
            "items": [
                {"id": item.id, "w": item.w, "v": item.v}
                for item in self.items
            ],
        }
