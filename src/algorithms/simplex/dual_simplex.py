import math
from typing import List, Tuple, Dict, Any, Optional
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

        # Build individual rows of the constraint equations
        self.tableau: List[List[float]] = []
        for i in range(self.m):
            row = []
            # Decision variables coefficients
            row.extend(A[i])
            # Slack variables coefficients (identity matrix)
            slacks = [0.0] * self.m
            slacks[i] = 1.0
            row.extend(slacks)
            # RHS value
            row.append(b[i])
            self.tableau.append(row)

        # Build the objective row (z - sum(c_j * x_j) = 0)
        obj_row = []
        obj_row.extend([-val for val in c])
        obj_row.extend([0.0] * self.m)
        obj_row.append(0.0)  # Initial objective value is 0.0
        self.tableau.append(obj_row)

        # Basis stores the index of the basic variable for each constraint row.
        # Initially, the basic variables are the slack variables (indices n to n+m-1).
        self.basis: List[int] = [self.n + i for i in range(self.m)]

    def pivot(self, row: int, col: int):
        """
        Performs a pivoting operation on the specified cell (row, col).
        Updates all other rows and updates the basis.
        Performs natural row operations on all columns and applies precision cleanup.
        """
        pivot_val = self.tableau[row][col]
        
        # 1. Normalize the pivot row
        self.tableau[row] = [val / pivot_val for val in self.tableau[row]]

        # 2. Eliminate entries in other rows
        for r in range(self.m + 1):
            if r != row:
                factor = self.tableau[r][col]
                for c in range(len(self.tableau[r])):
                    self.tableau[r][c] -= factor * self.tableau[row][c]

        # 3. Apply standard floating-point cleanups to prevent float precision drift
        for r in range(len(self.tableau)):
            for c in range(len(self.tableau[r])):
                if abs(self.tableau[r][c]) < 1e-12:
                    self.tableau[r][c] = 0.0
                elif abs(self.tableau[r][c] - 1.0) < 1e-12:
                    self.tableau[r][c] = 1.0

        # 4. Update the basic variable index for this row
        self.basis[row] = col

    def solve_primal(self, max_iterations: int = 1000) -> str:
        """
        Solves the LP relaxation using the Primal Simplex algorithm.
        Requires primal feasibility (b >= 0).
        """
        eps = 1e-9
        for _ in range(max_iterations):
            # Find entering variable (most negative coefficient in objective row)
            entering_col = -1
            min_val = -eps
            for c in range(self.n + self.m):
                if self.tableau[self.m][c] < min_val:
                    min_val = self.tableau[self.m][c]
                    entering_col = c

            if entering_col == -1:
                return "optimal"  # No negative coefficients in objective row

            # Find leaving variable (Minimum Ratio Test)
            leaving_row = -1
            min_ratio = float('inf')
            for r in range(self.m):
                val = self.tableau[r][entering_col]
                if val > eps:
                    ratio = self.tableau[r][-1] / val
                    if ratio < min_ratio:
                        min_ratio = ratio
                        leaving_row = r

            if leaving_row == -1:
                return "unbounded"  # LP objective is unbounded

            self.pivot(leaving_row, entering_col)

        return "max_iterations"

    def solve_dual(self, max_iterations: int = 1000) -> str:
        """
        Solves the LP using the Dual Simplex algorithm.
        Assumes dual feasibility (objective row non-negative for non-basic cols).
        Corrects primal infeasibility (negative RHS values).
        """
        eps = 1e-9
        for _ in range(max_iterations):
            # Find leaving row (most negative RHS value)
            leaving_row = -1
            min_rhs = -eps
            for r in range(self.m):
                if self.tableau[r][-1] < min_rhs:
                    min_rhs = self.tableau[r][-1]
                    leaving_row = r

            if leaving_row == -1:
                return "optimal"  # All RHS >= 0, primal feasible!

            # Find entering column (Dual ratio test)
            entering_col = -1
            min_ratio = float('inf')
            for c in range(self.n + self.m):
                val = self.tableau[leaving_row][c]
                if val < -eps:
                    # Ratio: objective row value / absolute of constraint row value
                    ratio = self.tableau[self.m][c] / -val
                    if ratio < min_ratio:
                        min_ratio = ratio
                        entering_col = c

            if entering_col == -1:
                return "infeasible"  # Primal LP is infeasible

            self.pivot(leaving_row, entering_col)

        return "max_iterations"

    def add_constraint(self, coeff: List[float], rhs: float):
        """
        Adds a new inequality constraint (cut) to the active tableau.
        coeff: coefficients for all existing columns (length self.n + self.m)
        rhs: right-hand side limit of the new inequality
        """
        new_slack_col = self.n + self.m

        # Insert 0.0 at the new slack column position for all existing rows
        for r in range(self.m + 1):
            self.tableau[r].insert(new_slack_col, 0.0)

        # Build the new constraint row:
        # Includes original coefficients, 0s for previous slacks, 1.0 for new slack, and the RHS
        new_row = []
        new_row.extend(coeff)
        new_row.append(1.0)
        new_row.append(rhs)

        # Canonicalize the new row against existing basic variables
        for r in range(self.m):
            basic_col = self.basis[r]
            factor = new_row[basic_col]
            if abs(factor) > 1e-12:
                for c in range(len(new_row)):
                    new_row[c] -= factor * self.tableau[r][c]
                    
        # Apply standard floating-point cleanup
        for c in range(len(new_row)):
            if abs(new_row[c]) < 1e-12:
                new_row[c] = 0.0

        # Insert the row just above the objective row
        self.tableau.insert(self.m, new_row)
        self.m += 1

        # Add the new slack variable to the basis
        self.basis.append(new_slack_col)

    def get_solution(self) -> List[float]:
        """
        Extracts current values of the decision variables.
        """
        sol = [0.0] * self.n
        for r in range(self.m):
            var_idx = self.basis[r]
            if var_idx < self.n:
                sol[var_idx] = self.tableau[r][-1]
        return sol

    def get_objective_value(self) -> float:
        """
        Extracts the objective function value.
        """
        return self.tableau[self.m][-1]


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
                
            # Phase II: Restore original objective and Canonicalize
            self.tableau.tableau[-1] = [-val for val in c] + [0.0] * self.tableau.m + [0.0]
            
            for r in range(self.tableau.m):
                basic_col = self.tableau.basis[r]
                factor = self.tableau.tableau[-1][basic_col]
                if abs(factor) > 1e-12:
                    for col in range(len(self.tableau.tableau[-1])):
                        self.tableau.tableau[-1][col] -= factor * self.tableau.tableau[r][col]
                        
            # Clean up precision
            for col in range(len(self.tableau.tableau[-1])):
                if abs(self.tableau.tableau[-1][col]) < 1e-12:
                    self.tableau.tableau[-1][col] = 0.0
                    
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
        
        # Update the RHS column for all rows (including objective row)
        for r in range(self.tableau.m + 1):
            self.tableau.tableau[r][-1] += delta * self.tableau.tableau[r][slack_col]
            
            if abs(self.tableau.tableau[r][-1]) < 1e-12:
                self.tableau.tableau[r][-1] = 0.0
                
        return self.tableau.solve_dual()

    def update_objective(self, col_idx: int, delta: float) -> str:
        """
        Updates the objective function coefficient of the variable at col_idx by delta.
        Then re-optimizes using Primal Simplex if necessary.
        """
        if self.tableau is None:
            return "error"
            
        self.tableau.tableau[-1][col_idx] -= delta
        
        # If the variable is currently in the basis, restore canonical form
        for r in range(self.tableau.m):
            if self.tableau.basis[r] == col_idx:
                for c in range(len(self.tableau.tableau[-1])):
                    self.tableau.tableau[-1][c] += delta * self.tableau.tableau[r][c]
                break
                
        for c in range(len(self.tableau.tableau[-1])):
            if abs(self.tableau.tableau[-1][c]) < 1e-12:
                self.tableau.tableau[-1][c] = 0.0
                
        return self.tableau.solve_primal()
        
    def add_constraint_and_reoptimize(self, coeff: List[float], rhs: float) -> str:
        """
        Adds a new constraint and re-optimizes the solution using Dual Simplex.
        """
        if self.tableau is None:
            return "error"
            
        self.tableau.add_constraint(coeff, rhs)
        return self.tableau.solve_dual()
