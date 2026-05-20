import math
import random
from abc import ABC, abstractmethod


class AcceptanceCriterion(ABC):
    """
    Lop co so truu tuong cho tieu chi chap nhan loi giai moi.
    Ke thua de tao tieu chi khac (Record-to-Record, Threshold, ...).
    """

    @abstractmethod
    def accept(self, current_value: float, new_value: float, rng: random.Random) -> bool:
        """Tra ve True neu chap nhan loi giai moi."""
        ...

    @abstractmethod
    def step(self) -> None:
        """Cap nhat trang thai sau moi iteration (vd: giam nhiet do)."""
        ...


class SimulatedAnnealing(AcceptanceCriterion):
    """
    Tieu chi Simulated Annealing cho bai toan TOI DA HOA.
    - Loi giai tot hon: luon chap nhan
    - Loi giai te hon: chap nhan voi xac suat exp(delta / T)
    """

    def __init__(self, start_temp: float, end_temp: float, cooling_rate: float):
        self.temperature = start_temp
        self.end_temp = end_temp
        self.cooling_rate = cooling_rate

    def accept(self, current_value: float, new_value: float, rng: random.Random) -> bool:
        if new_value >= current_value:
            return True
        if self.temperature <= 1e-10:
            return False
        delta = new_value - current_value  # am khi te hon
        return rng.random() < math.exp(delta / self.temperature)

    def step(self) -> None:
        self.temperature = max(self.end_temp, self.temperature * self.cooling_rate)
