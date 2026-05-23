from typing import List, Tuple

from src.models import KnapsackInstance, Item
from src.algorithms.base import (
    BaseKnapsackSolver,
    ZeroOneKnapsackMixin,
    UnboundedKnapsackMixin,
)


class DPKnapsackSolver(BaseKnapsackSolver, ZeroOneKnapsackMixin, UnboundedKnapsackMixin):
    """
    Quy hoach dong (Dynamic Programming) cho bai toan Knapsack.
    Ho tro: 0/1 Knapsack va Unbounded Knapsack.

    Luu y: DP yeu cau weight va capacity la so nguyen.
    Neu la float, se duoc lam tron bang int().

    Do phuc tap:
        0/1:        O(n * W) thoi gian, O(n * W) bo nho
        Unbounded:  O(n * W) thoi gian, O(W) bo nho
    """

    def solve_zero_one(self) -> Tuple[float, List[Item]]:
        """
        0/1 Knapsack bang QHD bottom-up.
        dp[i][w] = gia tri lon nhat dung i vat pham dau voi suc chua w.
        """
        items = self.instance.items
        n = len(items)
        W = int(self.instance.capacity)

        # Bang QHD 2 chieu
        dp = [[0.0] * (W + 1) for _ in range(n + 1)]

        for i in range(1, n + 1):
            item = items[i - 1]
            wi = int(item.weight)
            for w in range(W + 1):
                dp[i][w] = dp[i - 1][w]
                if wi <= w and dp[i - 1][w - wi] + item.value > dp[i][w]:
                    dp[i][w] = dp[i - 1][w - wi] + item.value

        # Truy vet
        selected: List[Item] = []
        w = W
        for i in range(n, 0, -1):
            if dp[i][w] != dp[i - 1][w]:
                selected.append(items[i - 1])
                w -= int(items[i - 1].weight)

        return dp[n][W], selected

    def solve_unbounded(self) -> Tuple[float, List[Tuple[Item, int]]]:
        """
        Unbounded Knapsack bang QHD.
        dp[w] = gia tri lon nhat voi suc chua w (moi vat pham duoc chon nhieu lan).
        """
        items = self.instance.items
        W = int(self.instance.capacity)

        dp = [0.0] * (W + 1)
        choice = [-1] * (W + 1)

        for w in range(1, W + 1):
            for idx, item in enumerate(items):
                wi = int(item.weight)
                if wi <= w and dp[w - wi] + item.value > dp[w]:
                    dp[w] = dp[w - wi] + item.value
                    choice[w] = idx

        # Truy vet so luong moi vat pham
        quantities: dict[int, int] = {}
        w = W
        while w > 0 and choice[w] != -1:
            idx = choice[w]
            quantities[idx] = quantities.get(idx, 0) + 1
            w -= int(items[idx].weight)

        selected = [(items[idx], qty) for idx, qty in quantities.items()]
        return dp[W], selected
