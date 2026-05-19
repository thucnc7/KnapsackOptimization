from typing import Optional

from src.mdmkp.models import MDMKPInstance, MDMKPSolution
from src.algorithms.alns.core import ALNSEngine, ALNSConfig, ALNSResult
from src.algorithms.alns.acceptance import SimulatedAnnealing
from src.algorithms.mdmkp.destroy_operators import RandomRemoval, WorstRemoval, RelatedRemoval
from src.algorithms.mdmkp.repair_operators import GreedyInsert, RegretInsert, RandomInsert
from src.algorithms.mdmkp.greedy import GreedyMDMKP


class MDMKPALNSSolver:
    """
    ALNS solver cho bai toan MDMKP.
    Ket hop: Greedy (khoi tao) + ALNS (cai tien) + SA (chap nhan).

    Su dung:
        solver = MDMKPALNSSolver(instance)
        result = solver.solve()
        print(result.best_value, result.best_solution)
    """

    def __init__(self, instance: MDMKPInstance, config: Optional[ALNSConfig] = None):
        self.instance = instance
        self.config = config or ALNSConfig()

    def solve(self) -> ALNSResult:
        # Buoc 1: Loi giai khoi tao bang Greedy
        initial = GreedyMDMKP(self.instance).solve()

        # Buoc 2: Cau hinh Simulated Annealing
        # Nhiet do ban dau = 5% gia tri greedy (cho phep chap nhan loi giai te hon ~5%)
        initial_temp = initial.total_value * 0.05 if initial.total_value > 0 else 100.0
        acceptance = SimulatedAnnealing(
            start_temp=initial_temp,
            end_temp=0.01,
            cooling_rate=0.9997,
        )

        # Buoc 3: Tao ALNS engine voi 3 destroy + 3 repair operators
        engine = ALNSEngine(
            destroy_operators=[
                RandomRemoval(),
                WorstRemoval(),
                RelatedRemoval(),
            ],
            repair_operators=[
                GreedyInsert(),
                RegretInsert(k=2),
                RandomInsert(),
            ],
            acceptance=acceptance,
            config=self.config,
        )

        # Buoc 4: Chay ALNS
        return engine.run(
            initial_solution=initial,
            objective_fn=lambda s: s.total_value,
            copy_fn=lambda s: s.copy(),
        )
