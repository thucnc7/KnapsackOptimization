import math
from dataclasses import dataclass
from typing import List, Union, TypedDict

@dataclass
class Item:
    """
    Represents an item in the Knapsack problem.
    """
    id: Union[int, str]
    weight: float
    value: float

    @property
    def density(self) -> float:
        """
        Calculate value density of the item (value / weight).
        Returns 0.0 if weight is 0.0.
        """
        if self.weight == 0:
            return 0.0
        return self.value / self.weight

    def __repr__(self) -> str:
        return f"Item(id={self.id}, weight={self.weight}, value={self.value}, density={self.density:.4f})"


class Metadata(TypedDict):
    """
    TypedDict for KnapsackInstance complexity metadata:
    - n (Quy mô không gian trạng thái): Số lượng vật phẩm. Quyết định số tầng duyệt của QHĐ (O(n)) và số nhánh tối đa của Quay lui/Nhánh cận (2^n).
    - capacity_ratio (Độ thắt nút tài nguyên): W / sum(w_i). Tỉ lệ này cho biết độ thắt nút của tài nguyên. 
      Khi tiến về 0.5, không gian tìm kiếm đạt cực đại (bài toán khó nhất).
      Khi tiến về 0 hoặc 1, không gian tìm kiếm bị thu hẹp đáng kể, các thuật toán DP/Nhánh cận chạy rất nhanh.
    - pearson_r (Hệ số tương quan Pearson): Mối quan hệ cấu trúc giữa Giá trị và Trọng lượng. 
      Phá hủy khả năng cắt nhánh của thuật toán Nhánh cận khi pearson_r tiến sát về 1.
    - density_cv (Hệ số biến thiên của mật độ giá trị - Coefficient of Variation): 
      CV = Độ lệch chuẩn mẫu của (v/w) / Trung bình của (v/w).
      CV càng nhỏ (các vật phẩm tốt ngang nhau), thuật toán Greedy càng dễ sai và Nhánh cận càng tốn thời gian.
    """
    n: int
    capacity_ratio: float
    pearson_r: float
    density_cv: float


class KnapsackInstance:
    """
    Represents an instance of the Knapsack Problem, including items, capacity, and complexity metadata.
    """
    def __init__(self, items: List[Item], capacity: float):
        self.items = items
        self.capacity = capacity
        self.metadata = self._calculate_metadata()

    def _calculate_metadata(self) -> Metadata:
        """
        Calculate instance complexity metadata metrics in pure Python.
        Optimized to use exactly two passes over the items list.
        """
        n = len(self.items)
        if n == 0:
            return {
                'n': 0,
                'capacity_ratio': 0.0,
                'pearson_r': 0.0,
                'density_cv': 0.0
            }

        # --- PASS 1: Accumulate sums to compute means ---
        total_weight = 0.0
        total_value = 0.0
        total_density = 0.0

        for item in self.items:
            total_weight += item.weight
            total_value += item.value
            total_density += item.density

        capacity_ratio = self.capacity / total_weight if total_weight > 0 else 0.0
        mean_w = total_weight / n
        mean_v = total_value / n
        mean_density = total_density / n

        # --- PASS 2: Compute deviations, Pearson correlation and density variance ---
        num_pearson = 0.0
        den_w = 0.0
        den_v = 0.0
        var_density = 0.0

        for item in self.items:
            dw = item.weight - mean_w
            dv = item.value - mean_v
            num_pearson += dw * dv
            den_w += dw * dw
            den_v += dv * dv
            
            dd = item.density - mean_density
            var_density += dd * dd

        # Pearson correlation
        if den_w == 0 or den_v == 0:
            pearson_r = 0.0
        else:
            pearson_r = num_pearson / math.sqrt(den_w * den_v)

        # Unbiased Coefficient of Variation (CV) using sample standard deviation (divided by n - 1)
        if n <= 1 or mean_density == 0:
            density_cv = 0.0
        else:
            var_d_sample = var_density / (n - 1)
            std_density = math.sqrt(max(0.0, var_d_sample))
            density_cv = std_density / mean_density

        return {
            'n': n,
            'capacity_ratio': capacity_ratio,
            'pearson_r': pearson_r,
            'density_cv': density_cv
        }

    def __repr__(self) -> str:
        return f"KnapsackInstance(n={len(self.items)}, capacity={self.capacity}, metadata={self.metadata})"
