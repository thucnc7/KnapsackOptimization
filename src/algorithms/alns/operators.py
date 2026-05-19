from abc import ABC, abstractmethod
from typing import Any
import random


class DestroyOperator(ABC):
    """
    Lop co so truu tuong cho Destroy operator.
    Nguoi dung ke thua va override __call__ de tao operator moi.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def __call__(self, solution: Any, rng: random.Random, degree: float) -> Any:
        """
        Pha huy mot phan loi giai.
        - solution: loi giai hien tai (se bi thay doi in-place)
        - rng: random generator
        - degree: ty le pha huy [0.0, 1.0]
        Tra ve solution da bi pha huy.
        """
        ...


class RepairOperator(ABC):
    """
    Lop co so truu tuong cho Repair operator.
    Nguoi dung ke thua va override __call__ de tao operator moi.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def __call__(self, solution: Any, rng: random.Random) -> Any:
        """
        Sua chua loi giai da bi pha huy.
        - solution: loi giai bi thieu (se bi thay doi in-place)
        - rng: random generator
        Tra ve solution da duoc sua chua.
        """
        ...
