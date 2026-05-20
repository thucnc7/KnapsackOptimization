import math
from typing import List, Tuple, Dict, Any, Optional
from src.models import KnapsackInstance, Item
from src.algorithms.base import ZeroOneKnapsackMixin
from src.algorithms.simplex.base_simplex import BaseSimplexSolver
from src.algorithms.simplex.dual_simplex import DualSimplexSolver

class GomoryCutSolver(ZeroOneKnapsackMixin, BaseSimplexSolver):
    """
    Gomory Cut Solver for the 0/1 Knapsack problem.
    Extends ZeroOneKnapsackMixin and BaseSimplexSolver.
    Uses Gomory cutting planes and Dual Simplex re-optimization to find integer optimal solutions.
    """
    def __init__(self, instance: KnapsackInstance, *args, **kwargs):
        """
        Initialize the Gomory Cut solver.
        Automatically instantiates a DualSimplexSolver to act as the continuous LP engine.
        """
        super().__init__(instance, *args, **kwargs)
        self.name: str = "Gomory Cut Solver"
        self.lp_solver = DualSimplexSolver(instance)

    def solve_zero_one(self) -> Tuple[float, List[Item]]:
        """
        Solves the 0/1 Knapsack problem using Gomory cutting planes.
        Iteratively identifies fractional decision variables in the optimal basis,
        generates the cutting plane constraint, inserts it into the tableau,
        and re-optimizes using Dual Simplex until an all-integer solution is achieved.

        Returns:
            Tuple[float, List[Item]]: Optimal integer value and list of selected items.
        """
        items = self.instance.items
        n = len(items)
        if n == 0 or self.instance.capacity <= 0:
            return 0.0, []

        # 1. Solve the initial continuous relaxation
        opt_val, selected = self.lp_solver.solve_fractional()

        # If the LP solver failed or is not optimal, return empty
        if self.lp_solver.tableau is None:
            return 0.0, []

        tableau = self.lp_solver.tableau
        eps = 1e-7

        # Numerical checker to determine if a float is practically fractional
        def is_fractional(val: float) -> bool:
            frac = val - math.floor(val)
            return eps < frac < 1.0 - eps

        while True:
            # Retrieve the current decision variables values
            sol = tableau.get_solution()

            # Find a fractional basic variable that corresponds to a decision variable
            fractional_row = -1
            for r in range(tableau.m):
                var_idx = tableau.basis[r]
                # We only perform cuts on decision variables (index < n)
                if var_idx < n:
                    val = tableau.tableau[r][-1]
                    if is_fractional(val):
                        fractional_row = r
                        break

            # If all decision variables are integers, we have found our integer optimal solution!
            if fractional_row == -1:
                break

            # Generate a Gomory Cut:
            #   -sum_{c} (f_rc * x_c) <= -f_r
            #   where f_rc = tableau[r][c] - floor(tableau[r][c])
            #   and f_r = tableau[r][-1] - floor(tableau[r][-1])
            coeff: List[float] = []
            num_cols = tableau.n + tableau.m
            for c in range(num_cols):
                val = tableau.tableau[fractional_row][c]
                f = val - math.floor(val)
                # Filter small numerical noise to avoid precision issues
                if f < eps or f > 1.0 - eps:
                    f = 0.0
                coeff.append(-f)

            rhs_val = tableau.tableau[fractional_row][-1]
            f_r = rhs_val - math.floor(rhs_val)
            rhs = -f_r

            # Add this cutting plane constraint to the active tableau
            tableau.add_constraint(coeff, rhs)

            # Re-optimize the primal infeasible but dual feasible tableau using Dual Simplex
            status = tableau.solve_dual()
            if status != "optimal":
                # Infeasible/Numerical failure - exit gracefully
                return 0.0, []

        # Extract the final integer optimal solution
        opt_val = tableau.get_objective_value()
        sol = tableau.get_solution()

        best_sol = []
        for i, item in enumerate(items):
            # Check if selected (fraction > 0.5 because it should be integer 0 or 1)
            if sol[i] > 0.5:
                best_sol.append(item)

        return opt_val, best_sol
