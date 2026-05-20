import random
from typing import List


class AdaptiveWeightManager:
    """
    Quan ly trong so thich nghi cho cac operator.
    Chon operator bang roulette wheel, cap nhat trong so theo hieu qua thuc te.

    Scoring:
        SIGMA_GLOBAL_BEST = 33  (tim duoc loi giai tot nhat moi)
        SIGMA_BETTER      = 9   (tot hon loi giai hien tai)
        SIGMA_ACCEPTED    = 13  (te hon nhung duoc chap nhan boi SA)
    """

    SIGMA_GLOBAL_BEST = 33
    SIGMA_BETTER = 9
    SIGMA_ACCEPTED = 13

    def __init__(self, operator_names: List[str], reaction_factor: float = 0.1):
        self.names = list(operator_names)
        self.reaction_factor = reaction_factor
        self.weights = {name: 1.0 for name in self.names}
        self._scores = {name: 0.0 for name in self.names}
        self._usage = {name: 0 for name in self.names}

    def select(self, rng: random.Random) -> str:
        """Chon operator bang roulette wheel theo trong so."""
        total = sum(self.weights.values())
        r = rng.random() * total
        cumulative = 0.0
        for name in self.names:
            cumulative += self.weights[name]
            if r <= cumulative:
                self._usage[name] += 1
                return name
        self._usage[self.names[-1]] += 1
        return self.names[-1]

    def update_score(self, name: str, sigma: float) -> None:
        """Cong diem cho operator sau moi iteration."""
        self._scores[name] += sigma

    def end_segment(self) -> None:
        """
        Ket thuc segment: cap nhat trong so theo cong thuc
        w_new = (1 - r) * w_old + r * (pi / theta)
        roi reset diem ve 0.
        """
        r = self.reaction_factor
        for name in self.names:
            if self._usage[name] > 0:
                avg_score = self._scores[name] / self._usage[name]
                self.weights[name] = (1 - r) * self.weights[name] + r * avg_score
            self.weights[name] = max(self.weights[name], 0.01)

        self._scores = {name: 0.0 for name in self.names}
        self._usage = {name: 0 for name in self.names}
