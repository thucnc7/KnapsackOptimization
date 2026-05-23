import math
from typing import List, Tuple, Dict, Any, Optional
from src.models import KnapsackInstance, Item
from src.algorithms.base import BaseKnapsackSolver

class BaseSimplexSolver(BaseKnapsackSolver):
    """
    Base solver for Simplex-based Knapsack algorithms.
    Implements cooperative multiple inheritance and handles formulation
    of the Knapsack problem as a standard Linear Programming (LP) model.
    """
    def __init__(self, instance: KnapsackInstance, *args, **kwargs):
        """
        Initialize the solver with a KnapsackInstance and set solver name.
        Cooperatively passes remaining arguments down the MRO chain.
        """
        self.name: str = "Base Simplex Solver"
        super().__init__(instance, *args, **kwargs)

    def _convert_to_lp_form(self, fixed_bounds: Optional[Dict[int, float]] = None) -> Tuple[List[List[float]], List[float], List[float]]:
        """
        Converts the KnapsackInstance problem parameters to standard Linear Programming form:
            Maximize c^T * x
            Subject to: A * x <= b
            and x >= 0

        If fixed_bounds is provided, it maps item index to a fixed value (0.0 or 1.0)
        to represent branching constraints in the Branch and Bound search tree.

        Returns:
            Tuple[List[List[float]], List[float], List[float]]:
                - A: Coefficient matrix of inequalities (size m x n)
                - b: Right-hand side bounds vector (size m)
                - c: Objective coefficients vector to maximize (size n)
        """
        items = self.instance.items
        n = len(items)
        W = self.instance.capacity

        # Objective coefficients are the values of each item
        c = [float(item.value) for item in items]

        # A and b will store constraints
        A: List[List[float]] = []
        b: List[float] = []

        # 1. Capacity Constraint: sum(w_i * x_i) <= W
        capacity_row = [float(item.weight) for item in items]
        A.append(capacity_row)
        b.append(float(W))

        # 2. Upper bounds: x_i <= 1 for 0-1 Knapsack (default or overridden by fixed_bounds)
        for i in range(n):
            if fixed_bounds is not None and i in fixed_bounds:
                val = fixed_bounds[i]
                if val == 0.0:
                    # x_i <= 0 (forces x_i = 0 since x_i >= 0 is implicit)
                    row = [0.0] * n
                    row[i] = 1.0
                    A.append(row)
                    b.append(0.0)
                else:
                    # Forces x_i = val by adding x_i <= val AND -x_i <= -val
                    row_ub = [0.0] * n
                    row_ub[i] = 1.0
                    A.append(row_ub)
                    b.append(float(val))

                    row_lb = [0.0] * n
                    row_lb[i] = -1.0
                    A.append(row_lb)
                    b.append(-float(val))
            else:
                # Default: 0 <= x_i <= 1
                row = [0.0] * n
                row[i] = 1.0
                A.append(row)
                b.append(1.0)

        # Apply Gaussian Elimination filter to remove redundant complex linear combinations
        A, b = self._filter_redundant_constraints(A, b)

        return A, b, c

    def _filter_redundant_constraints(self, A: List[List[float]], b: List[float]) -> Tuple[List[List[float]], List[float]]:
        """
        Remove duplicate constraints. For each unique coefficient pattern, keep the row
        with the tightest RHS (smallest b for `Ax <= b`). Two constraints are duplicates
        when their A-rows match coefficient-wise within `eps`.

        This is a safe simplification of the original Gaussian-elimination redundancy
        filter — for the Knapsack LP family (1 capacity row + n upper-bound rows of the
        form `x_i <= b_i`), every row is a unique standard basis vector except when the
        caller adds bounds for the same variable via `fixed_bounds`; in that case the
        tightest bound wins. General LP redundancy detection has worst-case O(n*m^3)
        cost and is unnecessary here.
        """
        if not A:
            return A, b

        eps = 1e-9

        def _key(row: List[float]) -> Tuple[int, ...]:
            return tuple(round(val / eps) for val in row)

        tightest: Dict[Tuple[int, ...], int] = {}
        for idx, row in enumerate(A):
            key = _key(row)
            prev = tightest.get(key)
            if prev is None or b[idx] < b[prev] - eps:
                tightest[key] = idx

        kept = sorted(tightest.values())
        return [A[i] for i in kept], [b[i] for i in kept]

