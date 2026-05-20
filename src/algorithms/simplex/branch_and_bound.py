import math
from typing import List, Tuple, Dict, Any, Optional
from src.models import KnapsackInstance, Item
from src.algorithms.base import ZeroOneKnapsackMixin, UnboundedKnapsackMixin
from src.algorithms.simplex.base_simplex import BaseSimplexSolver

class BranchAndBoundSimplexSolver(ZeroOneKnapsackMixin, UnboundedKnapsackMixin, BaseSimplexSolver):
    """
    Branch and Bound Controller Solver for Knapsack problems.
    Combines ZeroOne and Unbounded Mixins and utilizes continuous LP relaxation solves
    from the DualSimplexSolver to branch and prune.
    """
    def __init__(self, instance: KnapsackInstance, lp_solver_class=None, *args, **kwargs):
        """
        Initialize the Branch and Bound solver.
        lp_solver_class: The continuous LP solver class (defaults to DualSimplexSolver).
        """
        if lp_solver_class is None:
            from src.algorithms.simplex.dual_simplex import DualSimplexSolver
            lp_solver_class = DualSimplexSolver

        super().__init__(instance, *args, **kwargs)
        self.name: str = "Branch and Bound Simplex Solver"
        self.lp_solver = lp_solver_class(instance)

    def solve_zero_one(self) -> Tuple[float, List[Item]]:
        """
        Solves the 0/1 Knapsack problem using the Branch and Bound strategy
        operating over continuous relaxation solves of standard LP formulations.

        Returns:
            Tuple[float, List[Item]]: Best overall integer value and list of selected items.
        """
        items = self.instance.items
        n = len(items)
        if n == 0 or self.instance.capacity <= 0:
            return 0.0, []

        # Create quick index lookup mapping for item IDs
        id_to_idx = {item.id: idx for idx, item in enumerate(items)}

        # DFS stack contains states of variable bounds: Dict[item_index, fixed_value]
        stack: List[Dict[int, float]] = [{}]
        best_val: float = 0.0
        best_sol: List[Item] = []

        # Numerical tolerance checker for fractionality
        def is_fractional(val: float, eps: float = 1e-7) -> bool:
            frac = val - math.floor(val)
            return eps < frac < 1.0 - eps

        while stack:
            fixed_bounds = stack.pop()

            # 1. Solve LP relaxation for the current sub-problem node
            lp_val, lp_selected = self.lp_solver.solve_fractional(fixed_bounds)

            # 2. Pruning: If LP relaxation objective value is worse or equal to the best integer value, prune!
            if lp_val <= best_val + 1e-9:
                continue

            # 3. Reconstruct full decision vector
            sol = [0.0] * n
            for item, frac in lp_selected:
                idx = id_to_idx[item.id]
                sol[idx] = frac

            # 4. Find the first fractional variable to branch on
            split_idx = -1
            for i in range(n):
                if is_fractional(sol[i]):
                    split_idx = i
                    break

            if split_idx == -1:
                # Integer feasible node: Update global best integer solution
                if lp_val > best_val:
                    best_val = lp_val
                    best_sol = [items[i] for i in range(n) if sol[i] > 0.5]
            else:
                # Branch: Variable split_idx must be 0 or 1
                # Branch 1: x_split = 0
                fb0 = fixed_bounds.copy()
                fb0[split_idx] = 0.0

                # Branch 2: x_split = 1
                fb1 = fixed_bounds.copy()
                fb1[split_idx] = 1.0

                # Push branches to the search stack
                stack.append(fb0)
                stack.append(fb1)

        return best_val, best_sol
