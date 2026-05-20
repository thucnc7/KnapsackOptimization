from typing import List, Optional

from src.mdmkp.models import MDMKPInstance, MDMKPSolution, MDItem


class GreedyMDMKP:
    """
    Giai tham lam cho MDMKP.
    Sap xep item theo composite density (gia tri / tong trong luong chuan hoa),
    roi gan vao balo vua van nhat (best-fit).
    Dung lam loi giai khoi tao cho ALNS.
    """

    def __init__(self, instance: MDMKPInstance):
        self.instance = instance

    def solve(self) -> MDMKPSolution:
        solution = MDMKPSolution(self.instance)
        avg_caps = self._average_capacities()

        # Sap xep giam dan theo composite density
        ranked = sorted(
            range(self.instance.n_items),
            key=lambda i: self._composite_density(self.instance.items[i], avg_caps),
            reverse=True,
        )

        for item_idx in ranked:
            best_k = self._best_fit_knapsack(solution, item_idx)
            if best_k is not None:
                solution.insert_item(item_idx, best_k)

        return solution

    def _average_capacities(self) -> List[float]:
        """Tinh suc chua trung binh moi chieu tren tat ca balo."""
        n_dim = self.instance.n_dimensions
        avg = [0.0] * n_dim
        for k in self.instance.knapsacks:
            for d in range(n_dim):
                avg[d] += k.capacities[d]
        return [a / max(self.instance.n_knapsacks, 1) for a in avg]

    def _composite_density(self, item: MDItem, avg_caps: List[float]) -> float:
        """
        Density da chieu: value / sum(weight_d / avg_capacity_d).
        Chuan hoa trong luong theo suc chua trung binh de cac chieu co cung trong so.
        """
        normalized_sum = 0.0
        for d in range(self.instance.n_dimensions):
            if avg_caps[d] > 0:
                normalized_sum += item.weights[d] / avg_caps[d]
            else:
                return 0.0
        if normalized_sum <= 0:
            return float('inf')
        return item.value / normalized_sum

    def _best_fit_knapsack(self, solution: MDMKPSolution, item_idx: int) -> Optional[int]:
        """Tim balo co do vua van nhat (tong slack nho nhat)."""
        best_k = None
        best_slack = float('inf')

        for k in range(self.instance.n_knapsacks):
            if solution.can_insert(item_idx, k):
                slack = sum(solution.remaining_capacities[k])
                if slack < best_slack:
                    best_slack = slack
                    best_k = k

        return best_k
