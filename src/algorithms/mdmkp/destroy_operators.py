import random
from typing import List

from src.algorithms.alns.operators import DestroyOperator
from src.mdmkp.models import MDMKPSolution


class RandomRemoval(DestroyOperator):
    """Xoa ngau nhien q vat pham khoi loi giai."""

    def __init__(self):
        super().__init__("random_removal")

    def __call__(self, solution: MDMKPSolution, rng: random.Random, degree: float) -> MDMKPSolution:
        assigned = solution.get_assigned_items()
        if not assigned:
            return solution
        n_remove = max(1, int(len(assigned) * degree))
        to_remove = rng.sample(assigned, min(n_remove, len(assigned)))
        for idx in to_remove:
            solution.remove_item(idx)
        return solution


class WorstRemoval(DestroyOperator):
    """
    Xoa q vat pham co dong gop gia tri thap nhat.
    randomness cao -> chon ngau nhien hon; thap -> uu tien item te nhat.
    """

    def __init__(self, randomness: float = 3.0):
        super().__init__("worst_removal")
        self.randomness = randomness

    def __call__(self, solution: MDMKPSolution, rng: random.Random, degree: float) -> MDMKPSolution:
        assigned = solution.get_assigned_items()
        if not assigned:
            return solution
        n_remove = max(1, int(len(assigned) * degree))

        # Sap xep tang dan theo gia tri (item te nhat dau tien)
        items = solution.instance.items
        assigned_sorted = sorted(assigned, key=lambda i: items[i].value)

        removed = 0
        while removed < n_remove and assigned_sorted:
            # Chon thien vi ve phia dau (gia tri thap)
            pos = int(len(assigned_sorted) * (rng.random() ** self.randomness))
            pos = min(pos, len(assigned_sorted) - 1)
            solution.remove_item(assigned_sorted.pop(pos))
            removed += 1

        return solution


class RelatedRemoval(DestroyOperator):
    """
    Xoa q vat pham tuong tu nhau (gan nhau trong khong gian weight + value).
    Giai phong vung tai nguyen lien quan de tai cau truc.
    """

    def __init__(self, randomness: float = 3.0):
        super().__init__("related_removal")
        self.randomness = randomness

    def __call__(self, solution: MDMKPSolution, rng: random.Random, degree: float) -> MDMKPSolution:
        assigned = solution.get_assigned_items()
        if not assigned:
            return solution
        n_remove = max(1, int(len(assigned) * degree))
        items = solution.instance.items

        # Chon 1 item hat giong ngau nhien
        seed_idx = rng.choice(assigned)
        seed_item = items[seed_idx]

        # Sap xep theo do tuong dong (khoang cach L1 trong khong gian weight + value)
        def relatedness(i: int) -> float:
            item = items[i]
            w_dist = sum(abs(a - b) for a, b in zip(seed_item.weights, item.weights))
            v_dist = abs(seed_item.value - item.value)
            return w_dist + v_dist

        candidates = sorted([i for i in assigned if i != seed_idx], key=relatedness)

        to_remove = [seed_idx]
        for _ in range(n_remove - 1):
            if not candidates:
                break
            pos = int(len(candidates) * (rng.random() ** self.randomness))
            pos = min(pos, len(candidates) - 1)
            to_remove.append(candidates.pop(pos))

        for idx in to_remove:
            solution.remove_item(idx)

        return solution
