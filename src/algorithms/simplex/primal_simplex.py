import math
from typing import List, Tuple, Dict, Any, Optional
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

        # Construct Phase I Tableau
        # Columns:
        # - 0 to n-1: Decision variables
        # - n to n+m-1: Slack/Surplus variables
        # - n+m to n+m+num_art-1: Artificial variables
        # - n+m+num_art: RHS
        self.tableau: List[List[float]] = []
        for i in range(self.m):
            row = []
            # Multiply by -1 if RHS is negative to maintain non-negative RHS in Phase I
            multiplier = -1.0 if i in self.row_to_art else 1.0

            # Decision variables
            row.extend([val * multiplier for val in A[i]])

            # Slack/Surplus variables
            slacks = [0.0] * self.m
            slacks[i] = 1.0 * multiplier
            row.extend(slacks)

            # Artificial variables
            arts = [0.0] * self.num_art
            if i in self.row_to_art:
                art_idx = self.row_to_art[i]
                arts[art_idx] = 1.0
            row.extend(arts)

            # RHS
            row.append(b[i] * multiplier)
            self.tableau.append(row)

        # Initial basis setup
        self.basis: List[int] = []
        for i in range(self.m):
            if i in self.row_to_art:
                # Artificial variable is basic
                self.basis.append(self.n + self.m + self.row_to_art[i])
            else:
                # Slack variable is basic
                self.basis.append(self.n + i)

        # Construct Phase I auxiliary objective row: Maximize -sum(a_i)
        phase1_obj = [0.0] * (self.n + self.m)
        phase1_obj.extend([1.0] * self.num_art)
        phase1_obj.append(0.0)
        self.tableau.append(phase1_obj)

        # Make the Phase I objective row canonical by eliminating basic artificial variables
        for i in self.art_rows:
            for col in range(len(self.tableau[-1])):
                self.tableau[-1][col] -= self.tableau[i][col]

    def pivot(self, row: int, col: int):
        """
        Pivots the tableau at cell (row, col) and updates basic variables.
        Performs natural row operations on all columns and applies precision cleanup.
        """
        pivot_val = self.tableau[row][col]
        # Divide pivot row by pivot value
        self.tableau[row] = [val / pivot_val for val in self.tableau[row]]

        num_rows = len(self.tableau)
        for r in range(num_rows):
            if r != row:
                factor = self.tableau[r][col]
                for c in range(len(self.tableau[r])):
                    self.tableau[r][c] -= factor * self.tableau[row][c]

        # Apply standard floating-point cleanups to prevent float precision drift
        for r in range(len(self.tableau)):
            for c in range(len(self.tableau[r])):
                if abs(self.tableau[r][c]) < 1e-12:
                    self.tableau[r][c] = 0.0
                elif abs(self.tableau[r][c] - 1.0) < 1e-12:
                    self.tableau[r][c] = 1.0

        self.basis[row] = col

    def solve_primal(self, max_iterations: int = 1000) -> str:
        """
        Performs standard Primal Simplex iterations on the active tableau.
        """
        eps = 1e-9
        num_rows = len(self.tableau)
        obj_row_idx = num_rows - 1
        
        # Default active columns includes all variables except RHS. 
        # Phase II will override this via self.active_cols to ignore artificial variables
        if not hasattr(self, "active_cols"):
            self.active_cols = len(self.tableau[0]) - 1

        for _ in range(max_iterations):
            # Entering variable selection (most negative coefficient in objective row)
            entering_col = -1
            min_val = -eps
            for c in range(self.active_cols):
                if self.tableau[obj_row_idx][c] < min_val:
                    min_val = self.tableau[obj_row_idx][c]
                    entering_col = c

            if entering_col == -1:
                return "optimal"

            # Leaving variable selection (Primal ratio test)
            leaving_row = -1
            min_ratio = float('inf')
            for r in range(obj_row_idx):
                val = self.tableau[r][entering_col]
                if val > eps:
                    ratio = self.tableau[r][-1] / val
                    if ratio < min_ratio:
                        min_ratio = ratio
                        leaving_row = r

            if leaving_row == -1:
                return "unbounded"

            self.pivot(leaving_row, entering_col)

        return "max_iterations"

    def transition_to_phase_two(self, c_orig: List[float]):
        """
        Replaces the Phase I objective function with the original objective function c_orig,
        and restores canonical form. Retains artificial variables to handle degeneracy safely,
        but limits active columns to prevent them from entering the basis.
        """
        # 1. Drop the Phase I objective row
        self.tableau.pop()

        # 2. Inject original objective row (Maximize original objective)
        phase2_obj = []
        phase2_obj.extend([-val for val in c_orig]) # Decision variables
        phase2_obj.extend([0.0] * self.m)           # Slack variables
        phase2_obj.extend([0.0] * self.num_art)     # Artificial variables (kept but deactivated)
        phase2_obj.append(0.0)                      # RHS
        self.tableau.append(phase2_obj)

        # 3. Restore canonical form (basic variable coefficients in objective row must be 0)
        for i in range(self.m):
            basic_var = self.basis[i]
            
            factor = self.tableau[-1][basic_var]
            if abs(factor) > 1e-12:
                for col in range(len(self.tableau[-1])):
                    self.tableau[-1][col] -= factor * self.tableau[i][col]
                    
        # Apply standard floating-point cleanups
        for c in range(len(self.tableau[-1])):
            if abs(self.tableau[-1][c]) < 1e-12:
                self.tableau[-1][c] = 0.0

        # 4. Define active columns to restrict entering variable selection
        # (Only search over decision and slack variables, ignoring artificial variables)
        self.active_cols = self.n + self.m

    def get_solution(self) -> List[float]:
        sol = [0.0] * self.n
        for r in range(self.m):
            var_idx = self.basis[r]
            if var_idx < self.n:
                sol[var_idx] = self.tableau[r][-1]
        return sol

    def get_objective_value(self) -> float:
        return self.tableau[-1][-1]


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
