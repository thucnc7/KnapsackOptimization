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
        Uses Gaussian elimination to find and remove redundant complex linear combinations.
        For inequality systems (Ax <= b), a constraint is redundant if it can be expressed
        as a linear combination of other constraints with non-negative multipliers, and
        the resulting combined RHS is tighter than or equal to its own RHS.
        """
        if not A:
            return A, b
            
        n = len(A[0])
        m = len(A)
        eps = 1e-7
        
        filtered_A = []
        filtered_b = []
        
        for i in range(m):
            row_a = A[i]
            val_b = b[i]
            
            num_basis = len(filtered_A)
            if num_basis == 0:
                filtered_A.append(row_a)
                filtered_b.append(val_b)
                continue
                
            # Augmented matrix for Gaussian elimination: F^T | row_a^T
            # Size: n rows, num_basis + 1 columns
            aug = []
            for col in range(n):
                aug_row = [filtered_A[k][col] for k in range(num_basis)]
                aug_row.append(row_a[col])
                aug.append(aug_row)
                
            # Perform Gaussian Elimination
            rank = 0
            pivot_cols = []
            for col in range(num_basis):
                # Find pivot
                pivot_row = -1
                max_val = eps
                for r in range(rank, n):
                    if abs(aug[r][col]) > max_val:
                        max_val = abs(aug[r][col])
                        pivot_row = r
                
                if pivot_row == -1:
                    continue # Free variable
                    
                # Swap rows to bring pivot to current rank
                aug[rank], aug[pivot_row] = aug[pivot_row], aug[rank]
                
                # Normalize pivot row
                pivot_val = aug[rank][col]
                for c in range(col, num_basis + 1):
                    aug[rank][c] /= pivot_val
                    
                # Eliminate other rows
                for r in range(n):
                    if r != rank:
                        factor = aug[r][col]
                        for c in range(col, num_basis + 1):
                            aug[r][c] -= factor * aug[rank][c]
                            
                pivot_cols.append(col)
                rank += 1
                
            # Check if the system is consistent (i.e. row_a is a linear combination of F)
            is_dependent = True
            for r in range(rank, n):
                if abs(aug[r][-1]) > eps:
                    is_dependent = False
                    break
                    
            if is_dependent:
                # Extract the multipliers y
                y = [0.0] * num_basis
                for k, p_col in enumerate(pivot_cols):
                    y[p_col] = aug[k][-1]
                    
                # For inequalities, the combination is valid ONLY IF all multipliers are >= 0
                all_non_negative = all(val >= -eps for val in y)
                
                if all_non_negative:
                    # Check the RHS bound tightness
                    combined_rhs = sum(y[k] * filtered_b[k] for k in range(num_basis))
                    if combined_rhs <= val_b + eps:
                        # The constraint is mathematically redundant, skip adding it
                        continue
            
            # Keep the constraint if it is not redundant
            filtered_A.append(row_a)
            filtered_b.append(val_b)
            
        return filtered_A, filtered_b

