from typing import List, Tuple

from src.models import KnapsackInstance, Item
from src.algorithms.base import (
    BaseKnapsackSolver,
    ZeroOneKnapsackMixin,
    FractionalKnapsackMixin,
)


class GreedyKnapsackSolver(BaseKnapsackSolver, ZeroOneKnapsackMixin, FractionalKnapsackMixin):
    """
    Giai tham lam (Greedy) theo mat do gia tri (value / weight).

    Ho tro:
        Fractional Knapsack: toi uu (chon phan le cua item cuoi cung)
        0/1 Knapsack:        heuristic (khong dam bao toi uu)

    Do phuc tap: O(n log n) cho sap xep.
    """

    def solve_fractional(self) -> Tuple[float, List[Tuple[Item, float]]]:
        """
        Fractional Knapsack - GREEDY LA TOI UU cho bai toan nay.
        Sap xep theo density giam dan, chon toan bo hoac phan le.
        """
        sorted_items = sorted(self.instance.items, key=lambda x: x.density, reverse=True)
        remaining = self.instance.capacity
        selected: List[Tuple[Item, float]] = []
        total_value = 0.0

        for item in sorted_items:
            if remaining <= 0:
                break
            if item.weight <= remaining:
                selected.append((item, 1.0))
                total_value += item.value
                remaining -= item.weight
            else:
                fraction = remaining / item.weight
                selected.append((item, fraction))
                total_value += item.value * fraction
                remaining = 0.0

        return total_value, selected

    def solve_zero_one(self) -> Tuple[float, List[Item]]:
        """
        0/1 Knapsack bang Greedy - CHI LA HEURISTIC, khong dam bao toi uu.
        Sap xep theo density giam dan, chon nguyen item neu du suc chua.
        """
        sorted_items = sorted(self.instance.items, key=lambda x: x.density, reverse=True)
        remaining = self.instance.capacity
        selected: List[Item] = []
        total_value = 0.0

        for item in sorted_items:
            if item.weight <= remaining:
                selected.append(item)
                total_value += item.value
                remaining -= item.weight

        return total_value, selected
