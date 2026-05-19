import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from src.algorithms.alns.operators import DestroyOperator, RepairOperator
from src.algorithms.alns.acceptance import AcceptanceCriterion
from src.algorithms.alns.weight_manager import AdaptiveWeightManager


@dataclass
class ALNSConfig:
    """Cau hinh cho ALNS engine."""
    max_iterations: int = 10000
    segment_size: int = 100
    destroy_degree_min: float = 0.1
    destroy_degree_max: float = 0.4
    reaction_factor: float = 0.1
    seed: Optional[int] = None


@dataclass
class ALNSResult:
    """Ket qua tra ve tu ALNS engine."""
    best_solution: Any
    best_value: float
    iterations: int
    runtime: float
    destroy_weights: Dict[str, float] = field(default_factory=dict)
    repair_weights: Dict[str, float] = field(default_factory=dict)


class ALNSEngine:
    """
    ALNS Engine tong quat - khong phu thuoc vao bai toan cu the.
    Su dung bang cach truyen vao:
    - destroy_operators / repair_operators: cac operator cu the
    - acceptance: tieu chi chap nhan (SA, ...)
    - objective_fn: ham muc tieu (maximization)
    - copy_fn: ham sao chep loi giai
    """

    def __init__(
        self,
        destroy_operators: List[DestroyOperator],
        repair_operators: List[RepairOperator],
        acceptance: AcceptanceCriterion,
        config: Optional[ALNSConfig] = None,
    ):
        self.config = config or ALNSConfig()
        self.destroy_ops = {op.name: op for op in destroy_operators}
        self.repair_ops = {op.name: op for op in repair_operators}
        self.acceptance = acceptance

        self.destroy_weights = AdaptiveWeightManager(
            [op.name for op in destroy_operators],
            self.config.reaction_factor,
        )
        self.repair_weights = AdaptiveWeightManager(
            [op.name for op in repair_operators],
            self.config.reaction_factor,
        )

    def run(
        self,
        initial_solution: Any,
        objective_fn: Callable[[Any], float],
        copy_fn: Callable[[Any], Any],
    ) -> ALNSResult:
        """
        Chay vong lap ALNS chinh.
        - initial_solution: loi giai khoi tao (vd: tu Greedy)
        - objective_fn: ham tinh gia tri muc tieu (maximization)
        - copy_fn: ham deep copy loi giai
        """
        rng = random.Random(self.config.seed)
        cfg = self.config

        current = initial_solution
        current_value = objective_fn(current)
        best = copy_fn(current)
        best_value = current_value

        start_time = time.perf_counter()

        for iteration in range(1, cfg.max_iterations + 1):
            # Chon operator
            d_name = self.destroy_weights.select(rng)
            r_name = self.repair_weights.select(rng)

            # Destroy & Repair
            degree = rng.uniform(cfg.destroy_degree_min, cfg.destroy_degree_max)
            candidate = copy_fn(current)
            candidate = self.destroy_ops[d_name](candidate, rng, degree)
            candidate = self.repair_ops[r_name](candidate, rng)

            new_value = objective_fn(candidate)

            # Tinh diem cho operator
            sigma = 0.0
            if new_value > best_value:
                sigma = AdaptiveWeightManager.SIGMA_GLOBAL_BEST
                best = copy_fn(candidate)
                best_value = new_value
            elif new_value > current_value:
                sigma = AdaptiveWeightManager.SIGMA_BETTER
            elif self.acceptance.accept(current_value, new_value, rng):
                sigma = AdaptiveWeightManager.SIGMA_ACCEPTED

            # Chap nhan hoac tu choi
            if sigma > 0:
                current = candidate
                current_value = new_value

            self.destroy_weights.update_score(d_name, sigma)
            self.repair_weights.update_score(r_name, sigma)

            # Ha nhiet do
            self.acceptance.step()

            # Ket thuc segment -> cap nhat trong so
            if iteration % cfg.segment_size == 0:
                self.destroy_weights.end_segment()
                self.repair_weights.end_segment()

        runtime = time.perf_counter() - start_time

        return ALNSResult(
            best_solution=best,
            best_value=best_value,
            iterations=cfg.max_iterations,
            runtime=runtime,
            destroy_weights=dict(self.destroy_weights.weights),
            repair_weights=dict(self.repair_weights.weights),
        )
