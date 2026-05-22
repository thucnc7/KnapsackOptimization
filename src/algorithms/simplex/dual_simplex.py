import math
from typing import List, Tuple, Dict, Any, Optional

import numpy as np

from src.models import KnapsackInstance, Item
from src.algorithms.base import FractionalKnapsackMixin
from src.algorithms.simplex.base_simplex import BaseSimplexSolver

class SimplexTableau:
    """
    Represents a Simplex Tableau for solving Linear Programming (LP) problems.
    Supports both Primal Simplex and Dual Simplex operations, and dynamically
    adding constraints (cuts) to the active tableau.
    """
    def __init__(self, c: List[float], A: List[List[float]], b: List[float]):
        """
        Initialize the tableau:
            Maximize c^T * x
            Subject to A * x <= b
            and x >= 0

        Tableau shape: (m + 1) rows x (n + m + 1) columns
        - Row 0 to m-1: Constraints
        - Row m: Objective row (z - c^T * x = 0)
        - Column 0 to n-1: Decision variables
        - Column n to n+m-1: Slack variables
        - Column n+m: Right-Hand Side (RHS)
        """
        self.n: int = len(c)
        self.m: int = len(b)

        # Build numpy tableau (m+1 rows × n+m+1 cols)
        total_cols = self.n + self.m + 1
        tableau = np.zeros((self.m + 1, total_cols), dtype=float)
        for i in range(self.m):
            tableau[i, 0:self.n] = np.asarray(A[i], dtype=float)
            tableau[i, self.n + i] = 1.0
            tableau[i, -1] = b[i]
        tableau[-1, 0:self.n] = -np.asarray(c, dtype=float)
        self.tableau = tableau

        # Basis: initial basic variables are the slack vars (indices n .. n+m-1)
        self.basis: List[int] = [self.n + i for i in range(self.m)]

    def pivot(self, row: int, col: int):
        """Vectorized pivot: divide pivot row, subtract multiples from others, update basis."""
        pivot_val = self.tableau[row, col]
        self.tableau[row] = self.tableau[row] / pivot_val
        factors = self.tableau[:, col].copy()
        factors[row] = 0.0
        self.tableau -= np.outer(factors, self.tableau[row])
        self.tableau[row, col] = 1.0
        self.tableau[:row, col] = 0.0
        self.tableau[row + 1:, col] = 0.0
        self.basis[row] = col

    def solve_primal(self, max_iterations: int = 50000) -> str:
        """Vectorized Primal Simplex (requires primal feasibility b >= 0)."""
        eps = 1e-9
        for _ in range(max_iterations):
            obj = self.tableau[self.m, 0:self.n + self.m]
            entering_col = int(np.argmin(obj))
            if obj[entering_col] >= -eps:
                return "optimal"

            column = self.tableau[0:self.m, entering_col]
            rhs = self.tableau[0:self.m, -1]
            mask = column > eps
            if not mask.any():
                return "unbounded"
            ratios = np.where(mask, rhs / np.where(mask, column, 1.0), np.inf)
            leaving_row = int(np.argmin(ratios))

            self.pivot(leaving_row, entering_col)
        return "max_iterations"

    def solve_dual(self, max_iterations: int = 50000) -> str:
        """Vectorized Dual Simplex (requires dual feasibility)."""
        eps = 1e-9
        for _ in range(max_iterations):
            rhs_col = self.tableau[0:self.m, -1]
            leaving_row = int(np.argmin(rhs_col))
            if rhs_col[leaving_row] >= -eps:
                return "optimal"

            pivot_row = self.tableau[leaving_row, 0:self.n + self.m]
            obj_row = self.tableau[self.m, 0:self.n + self.m]
            mask = pivot_row < -eps
            if not mask.any():
                return "infeasible"
            ratios = np.where(mask, obj_row / np.where(mask, -pivot_row, 1.0), np.inf)
            entering_col = int(np.argmin(ratios))

            self.pivot(leaving_row, entering_col)
        return "max_iterations"

    def add_constraint(self, coeff: List[float], rhs: float):
        """Add a new inequality (cut) to the tableau."""
        new_slack_col = self.n + self.m

        # Insert a zero column at new_slack_col for all existing rows
        zero_col = np.zeros((self.tableau.shape[0], 1), dtype=float)
        self.tableau = np.hstack([
            self.tableau[:, :new_slack_col],
            zero_col,
            self.tableau[:, new_slack_col:],
        ])

        # Build new row: coeff | 1.0 (new slack) | rhs
        total_cols = self.tableau.shape[1]
        new_row = np.zeros(total_cols, dtype=float)
        new_row[:len(coeff)] = np.asarray(coeff, dtype=float)
        new_row[new_slack_col] = 1.0
        new_row[-1] = rhs

        # Canonicalize against current basic variables
        for r in range(self.m):
            basic_col = self.basis[r]
            factor = new_row[basic_col]
            if abs(factor) > 1e-12:
                new_row -= factor * self.tableau[r]

        # Insert above the objective row
        self.tableau = np.vstack([self.tableau[:self.m], new_row, self.tableau[self.m:]])
        self.m += 1
        self.basis.append(new_slack_col)

    def get_solution(self) -> List[float]:
        sol = [0.0] * self.n
        for r in range(self.m):
            var_idx = self.basis[r]
            if var_idx < self.n:
                sol[var_idx] = float(self.tableau[r, -1])
        return sol

    def get_objective_value(self) -> float:
        return float(self.tableau[self.m, -1])


class DualSimplexSolver(FractionalKnapsackMixin, BaseSimplexSolver):
    """
    Dual Simplex Solver for the continuous fractional Knapsack Problem.
    Extends FractionalKnapsackMixin and BaseSimplexSolver.
    """
    def __init__(self, instance: KnapsackInstance, *args, **kwargs):
        """
        Initialize the Dual Simplex solver.
        Uses cooperative inheritance to register with FractionalKnapsackMixin.
        """
        super().__init__(instance, *args, **kwargs)
        self.name: str = "Dual Simplex Solver"
        self.tableau: Optional[SimplexTableau] = None

    def solve_fractional(self, fixed_bounds: Optional[Dict[int, float]] = None) -> Tuple[float, List[Tuple[Item, float]]]:
        """
        Solves the continuous fractional LP relaxation of the knapsack problem.
        Exposes the final optimal SimplexTableau for downstream controllers (Gomory, Branch & Bound).
        """
        A, b, c = self._convert_to_lp_form(fixed_bounds)
        
        # Check if the initial state is Primal Feasible
        is_primal_feasible = all(val >= 0 for val in b)
        
        if is_primal_feasible:
            self.tableau = SimplexTableau(c, A, b)
            # Solve standard form using Primal Simplex (primal feasible, dual infeasible initially)
            status = self.tableau.solve_primal()
            if status != "optimal":
                return 0.0, []
        else:
            # Dual-Primal Two-Phase Method for Primal Infeasible initialization
            # Phase I: Set objective to 0 to make it Dual Feasible
            zero_c = [0.0] * len(c)
            self.tableau = SimplexTableau(zero_c, A, b)
            status = self.tableau.solve_dual()
            
            if status != "optimal":
                return 0.0, [] # Problem is mathematically infeasible
                
            # Phase II: Restore original objective and canonicalize
            total_cols = self.tableau.tableau.shape[1]
            new_obj = np.zeros(total_cols, dtype=float)
            new_obj[:self.tableau.n] = -np.asarray(c, dtype=float)
            self.tableau.tableau[-1] = new_obj
            for r in range(self.tableau.m):
                basic_col = self.tableau.basis[r]
                factor = self.tableau.tableau[-1, basic_col]
                if abs(factor) > 1e-12:
                    self.tableau.tableau[-1] -= factor * self.tableau.tableau[r]
                    
            status = self.tableau.solve_primal()
            if status != "optimal":
                return 0.0, []

        opt_val = self.tableau.get_objective_value()
        sol = self.tableau.get_solution()

        # Map variable outputs to their respective Item models and fractional proportions
        selected_items: List[Tuple[Item, float]] = []
        for i, item in enumerate(self.instance.items):
            fraction = sol[i]
            # Eliminate float arithmetic rounding inaccuracies
            if fraction < 1e-9:
                fraction = 0.0
            elif fraction > 1.0 - 1e-9:
                fraction = 1.0
                
            if fraction > 0.0:
                selected_items.append((item, fraction))

        return opt_val, selected_items

    def update_rhs(self, constraint_idx: int, delta: float) -> str:
        """
        Updates the RHS of the original constraint_idx by delta.
        Then re-optimizes using Dual Simplex if necessary.
        constraint_idx is the index of the original constraint (0 to m-1).
        """
        if self.tableau is None:
            return "error"
            
        # The original slack variable for constraint_idx was at column n + constraint_idx
        slack_col = self.tableau.n + constraint_idx
        self.tableau.tableau[:, -1] += delta * self.tableau.tableau[:, slack_col]
        return self.tableau.solve_dual()

    def update_objective(self, col_idx: int, delta: float) -> str:
        """
        Updates the objective function coefficient of the variable at col_idx by delta.
        Then re-optimizes using Primal Simplex if necessary.
        """
        if self.tableau is None:
            return "error"
            
        self.tableau.tableau[-1, col_idx] -= delta
        for r in range(self.tableau.m):
            if self.tableau.basis[r] == col_idx:
                self.tableau.tableau[-1] += delta * self.tableau.tableau[r]
                break
        return self.tableau.solve_primal()
        
    def add_constraint_and_reoptimize(self, coeff: List[float], rhs: float) -> str:
        """
        Adds a new constraint and re-optimizes the solution using Dual Simplex.
        """
        if self.tableau is None:
            return "error"
            
        self.tableau.add_constraint(coeff, rhs)
        return self.tableau.solve_dual()
