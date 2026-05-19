import random
from typing import List, Optional, Tuple

from src.algorithms.alns.operators import RepairOperator
from src.mdmkp.models import MDMKPSolution


def _best_fit_knapsack(solution: MDMKPSolution, item_idx: int) -> Optional[int]:
    """Tim balo co do vua vặn nhat (it du thua nhat) cho vat pham."""
    best_k = None
    best_slack = float('inf')
    item = solution.instance.items[item_idx]

    for k in range(solution.instance.n_knapsacks):
        if solution.can_insert(item_idx, k):
            slack = sum(
                solution.remaining_capacities[k][d] - item.weights[d]
                for d in range(solution.instance.n_dimensions)
            )
            if slack < best_slack:
                best_slack = slack
                best_k = k

    return best_k


class GreedyInsert(RepairOperator):
    """Chen tham lam: uu tien item gia tri cao, dat vao balo vua van nhat."""

    def __init__(self):
        super().__init__("greedy_insert")

    def __call__(self, solution: MDMKPSolution, rng: random.Random) -> MDMKPSolution:
        unassigned = solution.get_unassigned_items()
        items = solution.instance.items

        # Sap xep giam dan theo gia tri
        unassigned.sort(key=lambda i: items[i].value, reverse=True)

        for item_idx in unassigned:
            best_k = _best_fit_knapsack(solution, item_idx)
            if best_k is not None:
                solution.insert_item(item_idx, best_k)

        return solution


class RegretInsert(RepairOperator):
    """
    Chen theo do hoi han (regret-k).
    Item nao chi con it lua chon kha thi -> chen truoc (vi se mat co hoi).
    """

    def __init__(self, k: int = 2):
        super().__init__(f"regret_{k}_insert")
        self.k = k

    def __call__(self, solution: MDMKPSolution, rng: random.Random) -> MDMKPSolution:
        unassigned = list(solution.get_unassigned_items())

        while unassigned:
            best_item = None
            best_knapsack = None
            best_regret = -1.0

            for item_idx in unassigned:
                options = self._feasible_options(solution, item_idx)
                if not options:
                    continue

                # regret = slack(k-th best) - slack(best)
                # slack thap = vua van hon -> tot hon
                slacks = [s for _, s in options]
                if len(slacks) == 1:
                    regret = float('inf')  # chi 1 lua chon -> phai chen ngay
                else:
                    k_idx = min(self.k - 1, len(slacks) - 1)
                    regret = slacks[k_idx] - slacks[0]

                if regret > best_regret:
                    best_regret = regret
                    best_item = item_idx
                    best_knapsack = options[0][0]

            if best_item is None:
                break

            solution.insert_item(best_item, best_knapsack)
            unassigned.remove(best_item)

        return solution

    def _feasible_options(
        self, solution: MDMKPSolution, item_idx: int
    ) -> List[Tuple[int, float]]:
        """Tra ve danh sach (knapsack_idx, slack) sap xep tang dan theo slack."""
        item = solution.instance.items[item_idx]
        options = []
        for k in range(solution.instance.n_knapsacks):
            if solution.can_insert(item_idx, k):
                slack = sum(
                    solution.remaining_capacities[k][d] - item.weights[d]
                    for d in range(solution.instance.n_dimensions)
                )
                options.append((k, slack))
        options.sort(key=lambda x: x[1])  # slack thap = vua van hon = uu tien
        return options


class RandomInsert(RepairOperator):
    """Chen ngau nhien: thu tu ngau nhien, balo ngau nhien (neu kha thi)."""

    def __init__(self):
        super().__init__("random_insert")

    def __call__(self, solution: MDMKPSolution, rng: random.Random) -> MDMKPSolution:
        unassigned = solution.get_unassigned_items()
        rng.shuffle(unassigned)

        for item_idx in unassigned:
            feasible = [
                k for k in range(solution.instance.n_knapsacks)
                if solution.can_insert(item_idx, k)
            ]
            if feasible:
                solution.insert_item(item_idx, rng.choice(feasible))

        return solution
