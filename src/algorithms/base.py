from abc import ABC
import time
from typing import Dict, Any, List, Tuple

from src.models import KnapsackInstance, Item


class BaseKnapsackSolver(ABC):
    """
    Base class for Knapsack problem solvers.
    Maintains the shared knapsack instance and generic legacy compatibility interfaces.
    """
    def __init__(self, instance: KnapsackInstance, *args, **kwargs):
        """
        Initialize the solver with a KnapsackInstance.
        Consumes the instance argument and forwards remaining arguments to the next class in MRO.
        """
        self.instance: KnapsackInstance = instance
        
        # --- Legacy / Backward-Compatible Attributes ---
        self.status: str = "unsolved"
        self.runtime: float = 0.0
        self.best_value: float = 0.0
        self.best_weight: float = 0.0
        self.selected_items: List[Item] = []
        
        # Call the next initializer in the cooperative MRO chain (e.g., Mixin classes or object)
        super().__init__(*args, **kwargs)

    @property
    def supported_problems(self) -> List[str]:
        """
        Dynamically returns the list of knapsack problem variants supported by this solver instance.
        Recognized types: "zero_one", "unbounded", "fractional".
        """
        supported = []
        if isinstance(self, ZeroOneKnapsackMixin):
            supported.append("zero_one")
        if isinstance(self, UnboundedKnapsackMixin):
            supported.append("unbounded")
        if isinstance(self, FractionalKnapsackMixin):
            supported.append("fractional")
        return supported

    # =========================================================================
    # LEGACY / BACKWARD-COMPATIBLE METHODS
    # =========================================================================

    def solve(self) -> Tuple[float, List[Item]]:
        """
        Legacy method. Delegates to solve_zero_one() if the ZeroOneKnapsackMixin is supported.
        Otherwise, subclasses should implement/override this method.
        """
        if isinstance(self, ZeroOneKnapsackMixin):
            return self.solve_zero_one()
        raise NotImplementedError("Legacy solve() is not implemented on this class and ZeroOneKnapsackMixin is not supported.")

    def run(self) -> Dict[str, Any]:
        """
        Legacy template method. Delegates to run_zero_one() if ZeroOneKnapsackMixin is supported,
        or falls back to executing the custom solve() method if overridden.
        
        Returns:
            Dict[str, Any]: A solution summary containing details of the optimal state.
        """
        if isinstance(self, ZeroOneKnapsackMixin):
            return self.run_zero_one()
            
        # Fallback for pure legacy subclasses that only override solve() without Mixins
        if self.__class__.solve != BaseKnapsackSolver.solve:
            start_time = time.perf_counter()
            try:
                self.best_value, self.selected_items = self.solve()
                self.best_weight = sum(item.weight for item in self.selected_items)
                self.status = "optimal"
            except Exception as e:
                self.status = f"failed: {str(e)}"
                raise e
            finally:
                self.runtime = time.perf_counter() - start_time
            return self.get_solution_summary()
            
        raise NotImplementedError("This solver does not support ZeroOneKnapsackMixin or implement legacy solve().")

    def get_solution_summary(self) -> Dict[str, Any]:
        """
        Legacy method to get a summary of the solved knapsack instance.
        Delegates to get_zero_one_summary() if ZeroOneKnapsackMixin is supported.
        """
        if isinstance(self, ZeroOneKnapsackMixin):
            return self.get_zero_one_summary()
            
        # Fallback for pure legacy subclasses
        return {
            "status": self.status,
            "best_value": self.best_value,
            "best_weight": self.best_weight,
            "selected_ids": [item.id for item in self.selected_items],
            "runtime": self.runtime,
            "metadata": self.instance.metadata
        }


class ZeroOneKnapsackMixin:
    """
    Mixin class that adds 0/1 Knapsack solving capabilities to a solver.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.zero_one_status: str = "unsolved"
        self.zero_one_runtime: float = 0.0
        self.zero_one_best_value: float = 0.0
        self.zero_one_best_weight: float = 0.0
        self.zero_one_selected_items: List[Item] = []

    def solve_zero_one(self) -> Tuple[float, List[Item]]:
        """
        Solve the 0/1 Knapsack problem where each item can be selected at most once.
        Must be overridden by subclasses supporting 0/1 Knapsack.
        
        Returns:
            Tuple[float, List[Item]]: A tuple of (best_value, list_of_selected_items).
        """
        raise NotImplementedError("0/1 Knapsack solver is not implemented for this class.")

    def run_zero_one(self) -> Dict[str, Any]:
        """
        Execute the 0/1 Knapsack solver, track runtime, and update metrics.
        
        Returns:
            Dict[str, Any]: A solution summary containing details of the optimal state.
        """
        start_time = time.perf_counter()
        try:
            self.zero_one_best_value, self.zero_one_selected_items = self.solve_zero_one()
            self.zero_one_best_weight = sum(item.weight for item in self.zero_one_selected_items)
            self.zero_one_status = "optimal"
            
            # Sync to legacy attributes if present (since we use super().__init__ in cooperative MRO)
            if hasattr(self, 'status'):
                self.status = self.zero_one_status
                self.best_value = self.zero_one_best_value
                self.best_weight = self.zero_one_best_weight
                self.selected_items = self.zero_one_selected_items
        except NotImplementedError:
            self.zero_one_status = "not_implemented"
            if hasattr(self, 'status'):
                self.status = "not_implemented"
        except Exception as e:
            self.zero_one_status = f"failed: {str(e)}"
            if hasattr(self, 'status'):
                self.status = self.zero_one_status
            raise e
        finally:
            self.zero_one_runtime = time.perf_counter() - start_time
            if hasattr(self, 'runtime'):
                self.runtime = self.zero_one_runtime
            
        return self.get_zero_one_summary()

    def get_zero_one_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the solved 0/1 Knapsack instance.
        
        Returns:
            Dict[str, Any]: A dictionary containing solver statistics.
        """
        return {
            "status": self.zero_one_status,
            "best_value": self.zero_one_best_value,
            "best_weight": self.zero_one_best_weight,
            "selected_ids": [item.id for item in self.zero_one_selected_items],
            "runtime": self.zero_one_runtime,
            "metadata": self.instance.metadata
        }


class UnboundedKnapsackMixin:
    """
    Mixin class that adds Unbounded Knapsack solving capabilities to a solver.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unbounded_status: str = "unsolved"
        self.unbounded_runtime: float = 0.0
        self.unbounded_best_value: float = 0.0
        self.unbounded_best_weight: float = 0.0
        self.unbounded_selected_items: List[Tuple[Item, int]] = []

    def solve_unbounded(self) -> Tuple[float, List[Tuple[Item, int]]]:
        """
        Solve the Unbounded Knapsack problem where each item can be selected an infinite number of times.
        Must be overridden by subclasses supporting Unbounded Knapsack.
        
        Returns:
            Tuple[float, List[Tuple[Item, int]]]: A tuple of (best_value, list_of_tuples_of_selected_items_and_quantities).
        """
        raise NotImplementedError("Unbounded Knapsack solver is not implemented for this class.")

    def run_unbounded(self) -> Dict[str, Any]:
        """
        Execute the Unbounded Knapsack solver, track runtime, and update metrics.
        
        Returns:
            Dict[str, Any]: A solution summary containing details of the optimal state.
        """
        start_time = time.perf_counter()
        try:
            self.unbounded_best_value, self.unbounded_selected_items = self.solve_unbounded()
            self.unbounded_best_weight = sum(item.weight * qty for item, qty in self.unbounded_selected_items)
            self.unbounded_status = "optimal"
        except NotImplementedError:
            self.unbounded_status = "not_implemented"
        except Exception as e:
            self.unbounded_status = f"failed: {str(e)}"
            raise e
        finally:
            self.unbounded_runtime = time.perf_counter() - start_time
            
        return self.get_unbounded_summary()

    def get_unbounded_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the solved Unbounded Knapsack instance.
        
        Returns:
            Dict[str, Any]: A dictionary containing solver statistics.
        """
        return {
            "status": self.unbounded_status,
            "best_value": self.unbounded_best_value,
            "best_weight": self.unbounded_best_weight,
            "selected_items": [
                {"id": item.id, "quantity": qty}
                for item, qty in self.unbounded_selected_items
            ],
            "runtime": self.unbounded_runtime,
            "metadata": self.instance.metadata
        }


class FractionalKnapsackMixin:
    """
    Mixin class that adds Fractional Knapsack solving capabilities to a solver.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fractional_status: str = "unsolved"
        self.fractional_runtime: float = 0.0
        self.fractional_best_value: float = 0.0
        self.fractional_best_weight: float = 0.0
        self.fractional_selected_items: List[Tuple[Item, float]] = []

    def solve_fractional(self) -> Tuple[float, List[Tuple[Item, float]]]:
        """
        Solve the Fractional Knapsack problem where a fraction [0.0, 1.0] of each item can be selected.
        Must be overridden by subclasses supporting Fractional Knapsack.
        
        Returns:
            Tuple[float, List[Tuple[Item, float]]]: A tuple of (best_value, list_of_tuples_of_selected_items_and_fractions).
        """
        raise NotImplementedError("Fractional Knapsack solver is not implemented for this class.")

    def run_fractional(self) -> Dict[str, Any]:
        """
        Execute the Fractional Knapsack solver, track runtime, and update metrics.
        
        Returns:
            Dict[str, Any]: A solution summary containing details of the optimal state.
        """
        start_time = time.perf_counter()
        try:
            self.fractional_best_value, self.fractional_selected_items = self.solve_fractional()
            self.fractional_best_weight = sum(item.weight * frac for item, frac in self.fractional_selected_items)
            self.fractional_status = "optimal"
        except NotImplementedError:
            self.fractional_status = "not_implemented"
        except Exception as e:
            self.fractional_status = f"failed: {str(e)}"
            raise e
        finally:
            self.fractional_runtime = time.perf_counter() - start_time
            
        return self.get_fractional_summary()

    def get_fractional_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the solved Fractional Knapsack instance.
        
        Returns:
            Dict[str, Any]: A dictionary containing solver statistics.
        """
        return {
            "status": self.fractional_status,
            "best_value": self.fractional_best_value,
            "best_weight": self.fractional_best_weight,
            "selected_items": [
                {"id": item.id, "fraction": frac}
                for item, frac in self.fractional_selected_items
            ],
            "runtime": self.fractional_runtime,
            "metadata": self.instance.metadata
        }