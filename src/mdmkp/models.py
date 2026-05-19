from dataclasses import dataclass
from typing import List, Union


@dataclass
class MDItem:
    """
    Vat pham da chieu cho bai toan MDMKP.
    weights[d] = trong luong chieu thu d.
    """
    id: Union[int, str]
    weights: List[float]
    value: float

    def __repr__(self) -> str:
        return f"MDItem(id={self.id}, weights={self.weights}, value={self.value:.2f})"


@dataclass
class Knapsack:
    """
    Mot balo voi suc chua da chieu.
    capacities[d] = suc chua toi da chieu thu d.
    """
    id: Union[int, str]
    capacities: List[float]

    def __repr__(self) -> str:
        return f"Knapsack(id={self.id}, capacities={self.capacities})"


class MDMKPInstance:
    """
    Instance cua bai toan Multi-Dimensional Multiple Knapsack Problem.
    - items: danh sach vat pham da chieu
    - knapsacks: danh sach balo, moi balo co suc chua da chieu
    """
    def __init__(self, items: List[MDItem], knapsacks: List[Knapsack]):
        self.items = items
        self.knapsacks = knapsacks
        self.n_items = len(items)
        self.n_knapsacks = len(knapsacks)
        self.n_dimensions = len(knapsacks[0].capacities) if knapsacks else 0

    def __repr__(self) -> str:
        return (
            f"MDMKPInstance(items={self.n_items}, "
            f"knapsacks={self.n_knapsacks}, dimensions={self.n_dimensions})"
        )


class MDMKPSolution:
    """
    Loi giai cho MDMKP.
    - assignment[i] = chi so balo (0..m-1) hoac -1 (chua gan)
    - remaining_capacities[k][d] = suc chua con lai cua balo k chieu d
    - total_value = tong gia tri cac vat pham da gan
    """

    def __init__(self, instance: MDMKPInstance):
        self.instance = instance
        self.assignment: List[int] = [-1] * instance.n_items
        self.remaining_capacities: List[List[float]] = [
            list(k.capacities) for k in instance.knapsacks
        ]
        self.total_value: float = 0.0

    def can_insert(self, item_idx: int, knapsack_idx: int) -> bool:
        """Kiem tra vat pham co the chen vao balo khong (tat ca chieu deu du)."""
        item = self.instance.items[item_idx]
        remaining = self.remaining_capacities[knapsack_idx]
        return all(
            remaining[d] >= item.weights[d]
            for d in range(self.instance.n_dimensions)
        )

    def insert_item(self, item_idx: int, knapsack_idx: int) -> bool:
        """Chen vat pham vao balo. Tra ve False neu khong du suc chua."""
        if not self.can_insert(item_idx, knapsack_idx):
            return False
        item = self.instance.items[item_idx]
        for d in range(self.instance.n_dimensions):
            self.remaining_capacities[knapsack_idx][d] -= item.weights[d]
        self.assignment[item_idx] = knapsack_idx
        self.total_value += item.value
        return True

    def remove_item(self, item_idx: int) -> None:
        """Go vat pham khoi balo hien tai. Khong lam gi neu chua gan."""
        knapsack_idx = self.assignment[item_idx]
        if knapsack_idx == -1:
            return
        item = self.instance.items[item_idx]
        for d in range(self.instance.n_dimensions):
            self.remaining_capacities[knapsack_idx][d] += item.weights[d]
        self.assignment[item_idx] = -1
        self.total_value -= item.value

    def get_assigned_items(self) -> List[int]:
        return [i for i, k in enumerate(self.assignment) if k != -1]

    def get_unassigned_items(self) -> List[int]:
        return [i for i, k in enumerate(self.assignment) if k == -1]

    def copy(self) -> 'MDMKPSolution':
        new = MDMKPSolution.__new__(MDMKPSolution)
        new.instance = self.instance
        new.assignment = list(self.assignment)
        new.remaining_capacities = [list(row) for row in self.remaining_capacities]
        new.total_value = self.total_value
        return new

    def __repr__(self) -> str:
        assigned = sum(1 for a in self.assignment if a != -1)
        return (
            f"MDMKPSolution(assigned={assigned}/{self.instance.n_items}, "
            f"value={self.total_value:.2f})"
        )
