from typing import List, Tuple

from src.models import KnapsackInstance, Item
from src.algorithms.base import BaseKnapsackSolver, ZeroOneKnapsackMixin


class BranchAndBoundSolver(BaseKnapsackSolver, ZeroOneKnapsackMixin):
    """
    Nhanh can (Branch and Bound) cho 0/1 Knapsack.

    Duyet cay nhi phan (chon / khong chon), cat nhanh bang
    upper bound tu Fractional Knapsack relaxation.

    Do phuc tap: O(2^n) truong hop xau, nhung cat nhanh hieu qua
    giup giam dang ke trong thuc te.
    """

    def solve_zero_one(self) -> Tuple[float, List[Item]]:
        # Sap xep theo density giam dan de upper bound chat hon
        sorted_items = sorted(self.instance.items, key=lambda x: x.density, reverse=True)
        n = len(sorted_items)
        capacity = self.instance.capacity

        self._best_value = 0.0
        self._best_items: List[Item] = []

        def upper_bound(level: int, weight: float, value: float) -> float:
            """Tinh upper bound bang Fractional relaxation tu level tro di."""
            if weight > capacity:
                return 0.0
            bound = value
            remaining = capacity - weight
            for i in range(level, n):
                if sorted_items[i].weight <= remaining:
                    remaining -= sorted_items[i].weight
                    bound += sorted_items[i].value
                else:
                    bound += sorted_items[i].value * (remaining / sorted_items[i].weight)
                    break
            return bound

        def branch(level: int, weight: float, value: float, selected: List[Item]) -> None:
            if value > self._best_value:
                self._best_value = value
                self._best_items = list(selected)

            if level >= n:
                return

            item = sorted_items[level]

            # Nhanh CHON: thu them item nay
            if weight + item.weight <= capacity:
                selected.append(item)
                branch(level + 1, weight + item.weight, value + item.value, selected)
                selected.pop()

            # Nhanh KHONG CHON: chi di tiep neu upper bound con hua hen
            if upper_bound(level + 1, weight, value) > self._best_value:
                branch(level + 1, weight, value, selected)

        branch(0, 0.0, 0.0, [])
        return self._best_value, self._best_items
