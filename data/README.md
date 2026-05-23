# ⚙️ Data Management Component - Quản lý & Sinh dữ liệu thực nghiệm

Thư mục này quản lý cấu hình và tự động sinh tập dữ liệu thực nghiệm (Benchmark Datasets) cho các bài toán Cái túi (Knapsack Problem). Hệ thống hoạt động theo cơ chế **config-driven**, tách biệt hoàn toàn giữa cấu hình kịch bản và mã nguồn sinh dữ liệu.

---

## 🗺️ Điều hướng nhanh (Navigation)

- **Trang chủ dự án:** [README.md](../../README.md)
- **Mã nguồn tối ưu Python:** [KnapsackOptimization/README.md](../README.md)
  - 📊 [Phân tích & Đồ thị](../notebooks/README.md) - Thống kê và kiểm định thực nghiệm.
  - ⏱️ [Trình đo hiệu năng](../benchmark/README.md) - Hệ thống benchmark cô lập tiến trình.
  - ⚙️ [Quản lý dữ liệu](README.md) - Sinh dữ liệu theo phân phối Gauss.
  - 🌐 [Giao diện Webapp](../webapp/README.md) - Bảng điều khiển Flask tương tác.

---

## 1. Cấu hình kịch bản thực nghiệm (`test_scenarios.json`)

Tệp [`data/test_scenarios.json`](test_scenarios.json) định nghĩa danh sách các kịch bản sinh dữ liệu dưới dạng mảng JSON:

```json
[
  {
    "name": "benchmark_core",
    "description": "Mô tả kịch bản thực nghiệm chính",
    "n_values": [10, 50, 100, 500],
    "max_weight": 1000,
    "capacity_ratios": [0.1, 0.5, 0.9],
    "pearson_r_targets": [0.0, 0.5, 0.95],
    "instances_per_config": 5
  }
]
```

### Chi tiết các tham số cấu hình:

| Tham số | Bắt buộc | Mô tả |
| :--- | :---: | :--- |
| `name` | Có | Tên kịch bản (được dùng làm tiền tố đặt tên tệp dữ liệu). |
| `description` | Không | Mô tả ngắn gọn về mục tiêu của kịch bản thực nghiệm. |
| `n_values` | Có | Danh sách số lượng vật phẩm (các giá trị neo kích thước $n$). |
| `max_weight` | Không | Khối lượng tối đa có thể có của mỗi vật phẩm (mặc định: `1000`). |
| `capacity_ratios` | Có | Danh sách tỷ lệ sức chứa $W$ so với tổng khối lượng vật phẩm (các giá trị neo). |
| `pearson_r_targets` | Có | Hệ số tương quan Pearson đích giữa trọng lượng (`weight`) và giá trị (`value`). |
| `instances_per_config` | Có | Số lượng tệp testcase cần sinh cho mỗi tổ hợp tham số cấu hình. |

> [!TIP]
> **Ý nghĩa của hệ số tương quan Pearson đích (`pearson_r_targets`):**
> - `0.0` — Hoàn toàn ngẫu nhiên (không tương quan - uncorrelated).
> - `0.5` — Tương quan vừa phải/yếu (weakly correlated).
> - `0.95` — Tương quan rất cao (strongly correlated) — kịch bản này làm suy giảm đáng kể khả năng cắt tỉa nhanh của thuật toán nhánh cận (Branch & Bound).

---

## 2. Thực thi sinh dữ liệu (`generator.py`)

Khởi chạy script sinh dữ liệu từ thư mục **`KnapsackOptimization/`**:

```bash
# Chạy với seed mặc định (42) để kết quả sinh ra là giống nhau ở mọi máy
python data/generator.py --seed 42

# Chạy với hạt giống ngẫu nhiên tùy chọn khác
python data/generator.py --seed 123

# Chạy và nạp một tệp kịch bản cấu hình khác kèm seed xác định
python data/generator.py --config path/to/config.json --seed 42
```

> [!IMPORTANT]
> **Chú ý về tính nhất quán kết quả:** Nhằm đảm bảo mọi người thực thi mã nguồn đều thu được các tệp dữ liệu kiểm thử giống hệt nhau (giúp so sánh chính xác và minh bạch kết quả thời gian chạy và bộ nhớ), bạn **bắt buộc phải sử dụng cùng một tham số `--seed`** (ví dụ: `--seed 42`). Nếu không set seed hoặc dùng seed khác, dữ liệu sinh ra sẽ bị biến đổi ngẫu nhiên và dẫn đến sự sai lệch trong các biểu đồ phân tích hiệu năng.

### Các tùy chọn dòng lệnh (CLI Parameters):

| Tham số | Giá trị mặc định | Mô tả |
| :--- | :--- | :--- |
| `--config` | `data/test_scenarios.json` | Đường dẫn tới tệp cấu hình kịch bản thực nghiệm. |
| `--seed` | `42` | Hạt giống ngẫu nhiên toàn cục để đảm bảo tính tái tạo (reproducibility). |

### Chi tiết thuật toán sinh dữ liệu (Phiên bản v3)

#### 1. Gaussian Jitter (Nhiễu Gauss)
Mỗi tham số cấu hình trong tệp JSON được coi là một **giá trị neo (anchor)**. Nhằm tạo ra độ đa dạng tự nhiên, các giá trị thực tế của từng testcase sẽ được sinh lệch nhỏ xung quanh các neo đó theo phân phối chuẩn:
- $n_{actual} = \mathcal{N}(n_{anchor}, 0.10 \times n_{anchor})$ — giới hạn dưới (clamp) $\ge 2$.
- $ratio_{actual} = \mathcal{N}(ratio_{anchor}, 0.05 \times ratio_{anchor})$ — giới hạn trong khoảng (clamp) $[0.01, 1.0]$.

> [!NOTE]
> Cơ chế nhiễu Gauss tạo ra sự biến thiên liên tục quanh các neo giá trị gốc, giúp tập dữ liệu thực nghiệm mô phỏng tốt hơn các phân phối trong thực tế.

#### 2. Phân tích Cholesky (Cholesky Method)
Sử dụng phân tích ma trận Cholesky để kiểm soát hệ số tương quan Pearson mong muốn giữa Trọng lượng (`weight`) và Giá trị (`value`):
- Sinh hai biến ngẫu nhiên độc lập $x, z \sim \mathcal{N}(0, 1)$.
- Tạo biến phụ thuộc $y = r \cdot x + \sqrt{1 - r^2} \cdot z$ (với $r$ là hệ số Pearson mục tiêu).
- Co giãn (scale) tuyến tính các giá trị về đoạn $[1, max\_weight]$.

#### 3. Rejection Sampling (Lấy mẫu loại bỏ)
Khi yêu cầu hệ số tương quan đích $r \ge 0.9$, thuật toán tự động áp dụng vòng lặp lọc:
- Tính hệ số tương quan Pearson thực tế của tập vật phẩm vừa sinh bằng hàm `scipy.stats.pearsonr`.
- Nếu sai số tuyệt đối so với đích lớn hơn $0.03$, tập dữ liệu đó sẽ bị loại bỏ và hệ thống sẽ sinh lại từ đầu (thử lại tối đa $200$ lần).

---

## 3. Định dạng dữ liệu đầu ra (`data/raw/`)

Tên tệp JSON được đặt tự động theo quy ước:
```text
{scenario}_n{n_anchor}_wmax{max_weight}_cr{ratio_anchor}_pr{target_r}_{index}.json
```
*Ví dụ:* `benchmark_core_n100_wmax1000_cr0.5_pr0.95_03.json`

### Nội dung cấu trúc tệp JSON dữ liệu mẫu:

```json
{
  "test_id": "benchmark_core_n100_wmax1000_cr0.5_pr0.95_03",
  "capacity": 23514.7,
  "metadata": {
    "n": 110,
    "capacity_ratio": 0.5299,
    "pearson_r": 0.9643,
    "density_cv": 0.0964,
    "n_anchor": 100,
    "n_actual": 110,
    "target_pearson_r": 0.95,
    "capacity_ratio_anchor": 0.5,
    "capacity_ratio_actual": 0.5299,
    "max_weight": 1000,
    "seed": 42,
    "instance_seed": 42009377
  },
  "items": [
    {"id": 0, "weight": 180.0, "value": 794.0},
    {"id": 1, "weight": 420.5, "value": 850.0}
  ]
}
```

---

## 4. Kiểm tra chất lượng phân phối dữ liệu (`quality.py`)

Sau khi dữ liệu được sinh ra, chạy script phân tích để xác định chất lượng phân phối:

```bash
python data/quality.py --raw data/raw --output results/quality
```

Script sẽ vẽ một biểu đồ tổng hợp (dashboard) dạng lưới gồm 6 biểu đồ lưu vào tệp `results/quality/quality_dashboard.png`:

| Thứ tự | Loại đồ thị | Mục đích kiểm định |
| :---: | :--- | :--- |
| **1** | Histogram + Normal fit của $n_{actual}$ | Chứng minh các kích thước thực tế tuân theo phân phối Gauss quanh neo $n_{anchor}$. |
| **2** | Histogram + Normal fit của $ratio_{actual}$ | Chứng minh tỷ lệ sức chứa thực tế tuân theo phân phối Gauss quanh neo tỷ lệ đích. |
| **3** | Histogram + Normal fit của $pearson\_r$ | Chứng minh hệ số Pearson thực tế tập trung quanh các giá trị mục tiêu. |
| **4** | Đồ thị phân tán: $n_{anchor}$ vs $n_{actual}$ | Trực quan hóa biên độ biến động nhiễu của số lượng vật phẩm. |
| **5** | Đồ thị phân tán: $ratio_{anchor}$ vs $ratio_{actual}$ | Trực quan hóa biên độ biến động nhiễu của tỷ lệ sức chứa. |
| **6** | Đồ thị phân tán: $target\_r$ vs $actual\_r$ (theo $n$) | Đánh giá độ chính xác của tương quan Pearson thực tế (phân màu theo $n$). |

> [!NOTE]
> Trục hoành ($X$) của các đồ thị phân bố tần suất biểu thị giá trị thực tế đo được, trục tung ($Y$) biểu thị mật độ xác suất liên tục, kèm đường cong khớp lý thuyết (Normal fit line).

---

## 5. Ý nghĩa chi tiết các chỉ số trong khối `metadata`

### Chỉ số đặc trưng bài toán (tính toán thực tế từ dữ liệu):

| Chỉ số | Ý nghĩa đặc trưng thuật toán |
| :--- | :--- |
| `n` | Số lượng vật phẩm thực tế của testcase (sau khi áp dụng nhiễu Gaussian jitter). |
| `capacity_ratio` | Tỷ lệ sức chứa thực tế của túi: $W / \sum w_i$. |
| `pearson_r` | Hệ số tương quan Pearson thực tế giữa trọng lượng và giá trị của các vật phẩm. |
| `density_cv` | Hệ số biến thiên (Coefficient of Variation) của mật độ giá trị: $CV = \sigma(v/w) / \mu(v/w)$. Chỉ số $CV$ càng nhỏ nghĩa là mật độ giá trị càng sát nhau, làm giảm sức mạnh của thuật toán tham lam và tăng thời gian duyệt của nhánh cận. |

### Tham số neo cấu hình và thông tin truy vết:

| Chỉ số | Ý nghĩa kịch bản |
| :--- | :--- |
| `n_anchor` | Số lượng vật phẩm thiết kế ban đầu trong tệp cấu hình (neo). |
| `n_actual` | Số lượng vật phẩm thực tế được sinh ra. |
| `target_pearson_r` | Hệ số tương quan Pearson mục tiêu từ kịch bản. |
| `capacity_ratio_anchor` | Tỷ lệ sức chứa thiết kế ban đầu trong cấu hình. |
| `capacity_ratio_actual` | Tỷ lệ sức chứa thực tế của testcase. |
| `max_weight` | Trọng lượng tối đa của một vật phẩm theo thiết kế. |
| `seed` | Hạt giống ngẫu nhiên toàn cục của chương trình sinh dữ liệu. |
| `instance_seed` | Hạt giống ngẫu nhiên nội bộ dùng riêng cho việc tái tạo độc lập duy nhất testcase này. |
