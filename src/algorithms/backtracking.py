from typing import List, Tuple

from src.models import KnapsackInstance, Item
from src.algorithms.base import BaseKnapsackSolver, ZeroOneKnapsackMixin


class BacktrackingSolver(BaseKnapsackSolver, ZeroOneKnapsackMixin):
    """
    Quay lui (Backtracking) cho 0/1 Knapsack.

    Duyet tat ca to hop (chon / khong chon) voi cat tia don gian:
    neu tong gia tri con lai khong the vuot qua best hien tai -> bo qua.

    Do phuc tap: O(2^n) truong hop xau.
    Phu hop voi n nho (n <= 25).
    """

    def solve_zero_one(self) -> Tuple[float, List[Item]]:
        items = self.instance.items
        n = len(items)
        capacity = self.instance.capacity

        # Tinh truoc tong gia tri con lai tu moi vi tri (suffix sum)
        suffix_value = [0.0] * (n + 1)
        for i in range(n - 1, -1, -1):
            suffix_value[i] = suffix_value[i + 1] + items[i].value

        self._best_value = 0.0
        self._best_items: List[Item] = []

        def backtrack(level: int, weight: float, value: float, selected: List[Item]) -> None:
            if value > self._best_value:
                self._best_value = value
                self._best_items = list(selected)

            if level >= n:
                return

            # Cat tia: gia tri hien tai + tat ca con lai van khong vuot best
            if value + suffix_value[level] <= self._best_value:
                return

            item = items[level]

            # Chon item
            if weight + item.weight <= capacity:
                selected.append(item)
                backtrack(level + 1, weight + item.weight, value + item.value, selected)
                selected.pop()

            # Khong chon item
            backtrack(level + 1, weight, value, selected)

        backtrack(0, 0.0, 0.0, [])
        return self._best_value, self._best_items
