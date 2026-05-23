import math
from typing import List, Tuple, Dict, Any, Optional

import numpy as np

from src.models import KnapsackInstance, Item
from src.algorithms.base import FractionalKnapsackMixin
from src.algorithms.simplex.base_simplex import BaseSimplexSolver

class TwoPhaseTableau:
    """
    Represents a Simplex Tableau designed for the Two-Phase Simplex Method.
    Handles artificial variables and transitions between Phase I and Phase II.
    """
    def __init__(self, c: List[float], A: List[List[float]], b: List[float]):
        self.n: int = len(c)
        self.m: int = len(b)

        # Track which rows require artificial variables (i.e. those with negative RHS)
        self.row_to_art: Dict[int, int] = {}
        self.art_rows: List[int] = []
        for i in range(self.m):
            if b[i] < 0:
                self.row_to_art[i] = len(self.art_rows)
                self.art_rows.append(i)

        self.num_art: int = len(self.art_rows)

        # Construct Phase I Tableau via numpy for vectorized pivots downstream.
        # Columns: [decision (n) | slack (m) | artificial (num_art) | RHS (1)]
        total_cols = self.n + self.m + self.num_art + 1
        tableau = np.zeros((self.m + 1, total_cols), dtype=float)
        for i in range(self.m):
            multiplier = -1.0 if i in self.row_to_art else 1.0
            tableau[i, 0:self.n] = np.asarray(A[i], dtype=float) * multiplier
            tableau[i, self.n + i] = 1.0 * multiplier
            if i in self.row_to_art:
                tableau[i, self.n + self.m + self.row_to_art[i]] = 1.0
            tableau[i, -1] = b[i] * multiplier

        # Initial basis setup
        self.basis: List[int] = []
        for i in range(self.m):
            if i in self.row_to_art:
                self.basis.append(self.n + self.m + self.row_to_art[i])
            else:
                self.basis.append(self.n + i)

        # Construct Phase I auxiliary objective row: Maximize -sum(a_i)
        if self.num_art > 0:
            tableau[-1, self.n + self.m:self.n + self.m + self.num_art] = 1.0
            # Eliminate basic artificial variables from objective row (canonical form)
            for i in self.art_rows:
                tableau[-1] -= tableau[i]
        self.tableau = tableau

    def pivot(self, row: int, col: int):
        """Vectorized pivot: divide pivot row, then subtract multiples from other rows."""
        pivot_val = self.tableau[row, col]
        self.tableau[row] = self.tableau[row] / pivot_val
        factors = self.tableau[:, col].copy()
        factors[row] = 0.0
        self.tableau -= np.outer(factors, self.tableau[row])
        # Float precision cleanup — only the pivot column is guaranteed exact
        self.tableau[row, col] = 1.0
        self.tableau[:row, col] = 0.0
        self.tableau[row + 1:, col] = 0.0
        self.basis[row] = col

    def solve_primal(self, max_iterations: int = 50000) -> str:
        """Vectorized Primal Simplex iterations on the active tableau."""
        eps = 1e-9
        obj_row_idx = self.tableau.shape[0] - 1

        if not hasattr(self, "active_cols"):
            self.active_cols = self.tableau.shape[1] - 1

        for _ in range(max_iterations):
            obj = self.tableau[obj_row_idx, :self.active_cols]
            entering_col = int(np.argmin(obj))
            if obj[entering_col] >= -eps:
                return "optimal"

            column = self.tableau[:obj_row_idx, entering_col]
            rhs = self.tableau[:obj_row_idx, -1]
            mask = column > eps
            if not mask.any():
                return "unbounded"
            ratios = np.where(mask, rhs / np.where(mask, column, 1.0), np.inf)
            leaving_row = int(np.argmin(ratios))

            self.pivot(leaving_row, entering_col)

        return "max_iterations"

    def transition_to_phase_two(self, c_orig: List[float]):
        """Replace Phase I objective with Phase II objective; restore canonical form."""
        total_cols = self.tableau.shape[1]
        phase2_obj = np.zeros(total_cols, dtype=float)
        phase2_obj[:self.n] = -np.asarray(c_orig, dtype=float)
        self.tableau[-1] = phase2_obj

        # Restore canonical form: zero out objective-row coefficients of basic vars
        for i in range(self.m):
            basic_var = self.basis[i]
            factor = self.tableau[-1, basic_var]
            if abs(factor) > 1e-12:
                self.tableau[-1] -= factor * self.tableau[i]

        # Ignore artificial variables when selecting entering column in Phase II
        self.active_cols = self.n + self.m

    def get_solution(self) -> List[float]:
        sol = [0.0] * self.n
        for r in range(self.m):
            var_idx = self.basis[r]
            if var_idx < self.n:
                sol[var_idx] = float(self.tableau[r, -1])
        return sol

    def get_objective_value(self) -> float:
        return float(self.tableau[-1, -1])


class PrimalSimplexSolver(FractionalKnapsackMixin, BaseSimplexSolver):
    """
    Continuous LP Solver using the Primal Simplex Two-Phase Method.
    Extends FractionalKnapsackMixin and BaseSimplexSolver.
    """
    def __init__(self, instance: KnapsackInstance, *args, **kwargs):
        """
        Initialize the Primal Simplex Solver.
        Uses cooperative inheritance to register along MRO.
        """
        super().__init__(instance, *args, **kwargs)
        self.name: str = "Primal Simplex Solver"
        self.tableau: Optional[TwoPhaseTableau] = None

    def _phase_one(self, fixed_bounds: Optional[Dict[int, float]] = None) -> Tuple[str, TwoPhaseTableau, List[float]]:
        """
        Executes Phase I of the Two-Phase Method:
        Formulates and solves the auxiliary problem to find an initial Basic Feasible Solution (BFS).

        Returns:
            Tuple[status, tableau, original_objective]:
                - status: "feasible" or "infeasible"
                - tableau: Simplex tableau at completion of Phase I
                - original_objective: c coefficients for Phase II
        """
        A, b, c = self._convert_to_lp_form(fixed_bounds)
        tableau = TwoPhaseTableau(c, A, b)
        
        # If there are no artificial variables, the initial basis is already feasible!
        if tableau.num_art == 0:
            return "feasible", tableau, c
            
        status = tableau.solve_primal()
        if status != "optimal":
            return "infeasible", tableau, c

        # If the sum of artificial variables is > 0, the original problem is infeasible
        if tableau.get_objective_value() < -1e-7:
            return "infeasible", tableau, c

        return "feasible", tableau, c

    def _phase_two(self, initial_tableau: TwoPhaseTableau, c_orig: List[float]) -> str:
        """
        Executes Phase II of the Two-Phase Method:
        Transitions the tableau to the original objective function and pivots to optimal.

        Returns:
            str: Optimization status ("optimal", "unbounded", "max_iterations")
        """
        initial_tableau.transition_to_phase_two(c_orig)
        return initial_tableau.solve_primal()

    def solve_fractional(self, fixed_bounds: Optional[Dict[int, float]] = None) -> Tuple[float, List[Tuple[Item, float]]]:
        """
        Solves the continuous fractional LP relaxation of the knapsack problem.
        Utilizes the Two-Phase Method.

        Returns:
            Tuple[float, List[Tuple[Item, float]]]: Optimal value and list of item fractions.
        """
        # Phase I: Find a Basic Feasible Solution
        phase1_status, tableau, c_orig = self._phase_one(fixed_bounds)
        if phase1_status != "feasible":
            return 0.0, []

        self.tableau = tableau

        # Phase II: Solve original problem starting from Phase I BFS
        phase2_status = self._phase_two(self.tableau, c_orig)
        if phase2_status != "optimal":
            return 0.0, []

        opt_val = self.tableau.get_objective_value()
        sol = self.tableau.get_solution()

        # Map decisions back to original item structures
        selected_items: List[Tuple[Item, float]] = []
        for i, item in enumerate(self.instance.items):
            fraction = sol[i]
            if fraction < 1e-9:
                fraction = 0.0
            elif fraction > 1.0 - 1e-9:
                fraction = 1.0

            if fraction > 0.0:
                selected_items.append((item, fraction))

        return opt_val, selected_items
