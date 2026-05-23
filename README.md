# 🎒 Knapsack Optimization - Bộ công cụ tối ưu thực nghiệm bài toán Cái túi

Thư mục này chứa toàn bộ mã nguồn cài đặt thuật toán, trình sinh testcase ngẫu nhiên có ràng buộc chất lượng cao, hệ thống chạy benchmark độc lập phòng ngừa lỗi, mã phân tích/vẽ đồ thị thống kê phục vụ báo cáo, và **một webapp visualization tương tác** để khám phá kết quả benchmark cũng như chạy thử các thuật toán trực tiếp trong trình duyệt.

**Tác giả**: Nguyễn Hoàng Đạt · Lê Sỹ Thức · Nguyễn Hải Anh

---

## 🗂️ Giới thiệu cấu trúc repo

Repo được tổ chức theo nguyên tắc **tách biệt rõ ràng các lớp chức năng**: thuật toán (`src/`), sinh dữ liệu thực nghiệm (`data/`), khung benchmark (`benchmark/`), phân tích kết quả (`notebooks/`, `results/`), giao diện trực quan (`webapp/`), và tài liệu nghiên cứu (`plans/`). Mỗi lớp có thể chạy độc lập, đồng thời được liên kết qua một entry point thống nhất (`main.py`) và webapp.

| Thư mục | Vai trò | Khi nào cần đến |
| :--- | :--- | :--- |
| **`src/`** | Cài đặt thuật toán: base classes + mixins, basic solvers (Greedy, DP, Backtracking, BnB), Simplex family (Primal, Dual, BnB+Simplex, Gomory) | Khi mở rộng/sửa thuật toán hoặc thêm solver mới |
| **`data/`** | Sinh test instances theo `test_scenarios.json` (Gaussian jitter + rejection sampling), kiểm tra chất lượng phân phối, output JSON instances | Khi muốn tạo dữ liệu thực nghiệm mới hoặc verify chất lượng dataset |
| **`benchmark/`** | Runner độc lập process-isolated với timeout + OOM protection, đo wall time + peak memory bằng `tracemalloc` | Khi chạy benchmark trên toàn bộ test suite, output CSV |
| **`webapp/`** | Flask + vanilla JS + Chart.js dashboard với 7 modes, cho phép chạy live solver trong trình duyệt | Khi muốn khám phá kết quả tương tác, demo cho người khác xem |
| **`notebooks/`** | Sinh và execute Jupyter notebook tự động → xuất PNG (scatter, curve fitting, comparison plots) | Khi cần báo cáo định lượng dạng PDF/LaTeX với biểu đồ chất lượng publication |
| **`results/`** | Output: `csv/` (raw benchmark), `quality/` (phân tích dữ liệu), `plots/` (biểu đồ thực nghiệm) | Chứa và lưu trữ kết quả đầu ra của các đo đạc |
| **`plans/`** | Research reports về thuật toán (so sánh literature), implementation plans cho features mới | Khi nghiên cứu lý thuyết hoặc theo dõi quyết định thiết kế |
| **`main.py`** | Demo entry point: chạy 6 solvers trên 1 instance n=30, in bảng so sánh | Smoke test sau khi sửa code |

---

## 🗺️ Điều hướng nhanh (Navigation)

- **Trang chủ dự án:** [README.md](../README.md)
- **Mã nguồn tối ưu Python:** [KnapsackOptimization/README.md](README.md)
  - 📊 [Phân tích & Đồ thị](notebooks/README.md) - Thống kê và kiểm định thực nghiệm.
  - ⏱️ [Trình đo hiệu năng](benchmark/README.md) - Hệ thống benchmark cô lập tiến trình.
  - ⚙️ [Quản lý dữ liệu](data/README.md) - Sinh dữ liệu theo phân phối Gauss.
  - 🌐 [Giao diện Webapp](webapp/README.md) - Bảng điều khiển Flask tương tác.

---

## 🚀 Hướng dẫn khởi chạy nhanh (Quick Start)

Hãy đảm bảo rằng bạn đã kích hoạt môi trường ảo (ví dụ: `.venv`) và cài đặt đầy đủ các thư viện trong `requirements.txt` trước khi chạy các lệnh sau:

```bash
pip install -r requirements.txt
```

### 1. Sinh dữ liệu mẫu (Testcases Generation)

Dữ liệu thử nghiệm được cấu hình chi tiết tại [`data/test_scenarios.json`](data/test_scenarios.json). Trình sinh dữ liệu sử dụng phương pháp **Gaussian jitter** (tự động biến thiên ngẫu nhiên xung quanh các neo kích thước phần tử $N$, tỷ lệ sức chứa `capacity_ratio`) và cơ chế **rejection sampling** để lọc các cặp trọng lượng - giá trị có hệ số tương quan Pearson mong muốn ($r \ge 0.9$ hoặc tùy chọn khác).

```bash
# Sử dụng tham số --seed (ví dụ: --seed 42) để đảm bảo kết quả sinh ngẫu nhiên là đồng nhất và có thể tái lập
python data/generator.py --seed 42
```
> [!IMPORTANT]
> **Hạt giống ngẫu nhiên (Set Seed) & Tính tái lập kết quả:** Hãy luôn chỉ định rõ tham số `--seed 42` (hoặc một số hạt giống cụ thể) khi sinh dữ liệu. Việc này giúp đảm bảo toàn bộ tệp testcase JSON sinh ra sẽ giống hệt nhau ở mỗi lần chạy, giúp người khác tái lập chính xác kết quả đo đạc benchmark và phân tích thực nghiệm giống như bạn.

### 2. Kiểm tra chất lượng phân phối dữ liệu (Quality Check)

Để xác nhận xem dữ liệu sinh ra có tuân thủ phân phối chuẩn hình chuông Gauss quanh các giá trị neo và phân tán đồng đều hay không, hãy chạy script:

```bash
python data/quality.py --raw data/raw --output results/quality
```
> [!TIP]
> Biểu đồ phân phối Gauss và biểu đồ phân tán (scatter plot) sẽ được xuất ra thư mục `results/quality/`.

### 3. Thực thi Suite Benchmark hiệu năng

Chạy đo đạc thời gian thực thi (runtime) và lượng bộ nhớ tiêu thụ lớn nhất (peak memory) của từng thuật toán trên các testcase. Mỗi thuật toán được khởi chạy trên một tiến trình (process) độc lập để đảm bảo nếu xảy ra lỗi **TIMEOUT** hoặc **OOM** (hết bộ nhớ) ở một thuật toán, toàn bộ tiến trình benchmark vẫn tiếp tục hoàn thành bình thường.

```bash
python benchmark/runner.py --timeout 5 --output results/csv/benchmark_results.csv
```

**Các tham số dòng lệnh chính:**
- `--timeout`: Thời gian chạy tối đa cho mỗi bài toán (mặc định: `60` giây).
- `--limit`: Giới hạn số lượng testcase chạy thử (`0` = chạy tất cả).
- `--raw`: Thư mục chứa dữ liệu đầu vào (mặc định: `data/raw`).
- `--output`: File lưu kết quả benchmark dạng CSV.

### 4. Tự động sinh báo cáo đồ thị (Analysis & Plotting)

Sau khi có tệp `benchmark_results.csv`, bạn có thể vẽ toàn bộ các biểu đồ phân tích thực nghiệm chỉ bằng một dòng lệnh duy nhất:

```bash
python notebooks/execute_notebook.py
```

> [!NOTE]
> **Đồ thị xuất ra bao gồm:**
> - `scatter_{Algorithm}.png`: Đồ thị phân tán biểu diễn thời gian thực thi theo từng tham số (N, Tỷ lệ sức chứa, Hệ số Pearson).
> - `curvefit_{Algorithm}.png`: Đồ thị tự động tìm kiếm và vẽ đường cong tiệm cận thực nghiệm (Linear, Quadratic, Cubic, Exponential) kèm chỉ số chỉ định độ khớp $R^2$.
> - `algo_status_comparison.png`: Biểu đồ cột chồng thể hiện tỷ lệ Thành công / Quá giờ / Tràn bộ nhớ của từng thuật toán.
> - `memory_comparison.png`: Biểu đồ hộp (Box plot) so sánh bộ nhớ tiêu thụ đỉnh của các thuật toán trên thang đo log.
> - `runtime_comparison_01_exact.png`, `runtime_comparison_01_large.png`, `runtime_comparison_fractional.png`: So sánh thời gian chạy thực nghiệm trung vị của các thuật toán theo đúng nhóm bài toán.

### 5. Webapp Visualization (Tương tác)

Khởi động Flask webapp để khám phá dữ liệu benchmark, chạy live solver, và so sánh kết quả ngay trong trình duyệt:

```bash
python -m webapp.app --port 5000
```

Mở trình duyệt tại [http://127.0.0.1:5000](http://127.0.0.1:5000). Webapp cung cấp **7 chế độ chạy** trên cùng một giao diện SPA:

| Chế độ | Chức năng |
| :--- | :--- |
| **Dashboard** | Tổng quan CSV benchmark — success/timeout/error per algorithm, time/memory averages, thời gian theo N (log scale), bảng chi tiết. |
| **So sánh** | Paired comparison 2 thuật toán bất kỳ — scatter log-log thời gian, value khớp/lệch, speedup theo N. |
| **Single Solver** | Chọn 1 instance + 1 algorithm + timeout → chạy live với banner đếm thời gian + progress bar budget. Hiển thị capacity fill bar và scatter weight×value các items chọn/không chọn. |
| **Multi-Solver** | Streaming NDJSON: chạy nhiều thuật toán tuần tự trên 1 instance, mỗi algo emit `tick` mỗi 250ms để UI cập nhật badge realtime. |
| **Custom Instance** | Builder thủ công hoặc **sinh ngẫu nhiên** với config: N, max_weight, capacity_ratio, target Pearson r, seed. |
| **Data Quality** | Hiển thị `test_scenarios.json` + các biểu đồ chất lượng đã sinh ra. |
| **Job Runner** | Spawn nền `benchmark/runner.py`, `data/generator.py`, `data/quality.py` với log streaming + progress bar parse từ tqdm. |

Chi tiết xem tại [`webapp/README.md`](webapp/README.md).

---

## 📂 Sơ đồ các mô-đun chính

```text
KnapsackOptimization/
├── src/                        # Mã nguồn lõi thuật toán
│   ├── models.py               # Item, KnapsackInstance, metadata
│   └── algorithms/
│       ├── base.py             # BaseSolver + ZeroOne/Fractional/Unbounded mixins
│       ├── basic/              # Thuật toán exact cơ bản cho Knapsack
│       │   ├── greedy.py       # Greedy01 (heuristic) + GreedyFractional (LP optimal)
│       │   ├── dp.py           # Quy hoạch động (DP, DPUnbounded)
│       │   ├── backtracking.py # Quay lui có cắt tỉa
│       │   └── branch_and_bound.py # Nhánh cận với LP relaxation bound
│       └── simplex/            # LP solvers vectorized với numpy
│           ├── base_simplex.py        # LP form conversion + dedup constraints
│           ├── primal_simplex.py      # Two-Phase Primal Simplex
│           ├── dual_simplex.py        # Dual Simplex (cho re-optimization)
│           ├── branch_and_bound.py    # Simplex-based Branch & Bound (integer)
│           └── gomory_cut.py          # Gomory cutting planes
│
├── benchmark/                  # Benchmark runner độc lập
│   ├── runner.py               # Process-isolated với timeout/OOM handling
│   └── metrics.py              # tracemalloc + perf_counter wrapper
│
├── data/                       # Sinh dữ liệu + kiểm tra chất lượng
│   ├── generator.py            # Gaussian jitter + rejection sampling Pearson r
│   ├── quality.py              # Phân tích phân phối, vẽ heatmap/dashboard
│   ├── test_scenarios.json     # 4 kịch bản: core_exact, core_heuristic, stress, extreme_n
│   └── raw/                    # JSON instances sinh ra
│
├── webapp/                     # Flask + vanilla JS visualization SPA
│   ├── app.py                  # Entry point
│   ├── api/                    # 4 blueprints: benchmark, data, solver, runner
│   ├── static/                 # CSS + JS modules (Chart.js từ CDN)
│   └── templates/              # SPA-style index.html với mode switcher
│
├── notebooks/                  # Auto-generated analysis notebooks
│   ├── build_notebook.py       # Sinh `.ipynb` từ template
│   └── execute_notebook.py     # Run notebook → xuất PNG vào results/plots
│
├── results/                    # Output: csv, plots, quality images
├── plans/                      # Báo cáo nghiên cứu & Kế hoạch thực hiện
├── main.py                     # Demo nhỏ chạy 6 solvers trên 1 instance n=30
└── requirements.txt
```

---

## 🧮 Các thuật toán

### Phát biểu bài toán

**0/1 Knapsack** (bài toán cái túi 0/1) — cho $n$ vật phẩm, mỗi vật phẩm $i$ có trọng lượng $w_i > 0$ và giá trị $v_i > 0$, và một sức chứa $W$. Tìm tập con $S$ các vật phẩm sao cho:

$$\max \sum_{i \in S} v_i \quad \text{subject to} \quad \sum_{i \in S} w_i \leq W$$

Tương đương dạng chương trình tuyến tính nguyên (Integer Linear Programming):

$$\max \sum_{i=1}^{n} v_i x_i \quad \text{s.t.} \quad \sum_{i=1}^{n} w_i x_i \leq W,\ x_i \in \{0, 1\}$$

**Fractional Knapsack** thay $x_i \in \{0, 1\}$ bằng $0 \le x_i \le 1$, cho phép lấy một phần vật phẩm. Đây chính là **LP relaxation** của bài 0/1.

**Unbounded Knapsack** thay bằng $x_i \in \mathbb{Z}_+$ — mỗi vật phẩm có thể lấy số lần không giới hạn.

### Bảng tổng quan thuật toán

| Tên thuật toán | Loại | Khả dụng cho | Độ phức tạp lý thuyết | Tính tối ưu (Optimality) |
| :--- | :--- | :--- | :--- | :---: |
| `GreedyKnapsackSolver` | Tham lam | 0/1 + Fractional | $O(n \log n)$ | ✓ cho Fractional, ✗ cho 0/1 |
| `DPKnapsackSolver` | Pseudo-polynomial | 0/1 + Unbounded | $O(n \cdot W)$ | ✓ |
| `BacktrackingSolver` | Vét cạn cắt tỉa | 0/1 | $O(2^n)$ worst case | ✓ |
| `BranchAndBoundSolver` | Nhánh cận + LP | 0/1 | $O(2^n)$ worst, ~polynomial mean | ✓ |
| `PrimalSimplexSolver` | Two-Phase Simplex | Fractional (LP) | exponential worst, $\approx O(n^3)$ mean | ✓ |
| `DualSimplexSolver` | Dual Simplex | Fractional (LP) | exponential worst, $\approx O(n^3)$ mean | ✓ |
| `BranchAndBoundSimplexSolver` | Simplex + BnB | 0/1 integer | exponential | ✓ |
| `GomoryCutSolver` | Cutting planes + Dual Simplex | 0/1 integer | có thể không hội tụ | ✓ khi hội tụ |

---

### 1. `src/algorithms/basic/` — Thuật toán cơ bản

#### `greedy.py` — Tham lam (Greedy)
Sắp xếp vật phẩm giảm dần theo **mật độ giá trị** $v_i / w_i$, sau đó chọn lần lượt vật phẩm có mật độ cao nhất nếu còn vừa túi.
- **Fractional**: nếu vật phẩm cuối không vừa hết, lấy phần fractional cuối cho khít. Thuật toán này **tối ưu chứng minh được** cho LP relaxation (Dantzig 1957) — đây cũng chính là baseline ground-truth của project để verify các Simplex solvers.
- **0/1 Greedy**: dừng ngay khi vật phẩm tiếp theo không vừa. **Không tối ưu**, có thể sai lệch lớn (worst case approximation ratio = 1/2).

Độ phức tạp $O(n \log n)$ (chỉ tốn ở bước sắp xếp). Trên $n=1000$: thời gian thực thi cỡ $\sim 0.1\text{ms}$.

#### `dp.py` — Quy hoạch động (Dynamic Programming)
Bảng $dp[i][w]$ = giá trị tối đa khi xét $i$ vật phẩm đầu và sức chứa $w$. Quan hệ truy hồi:

$$dp[i][w] = \max\left( dp[i-1][w],\ dp[i-1][w-w_i] + v_i \right)$$

- **Pseudo-polynomial**: $O(n \cdot W)$ thời gian và bộ nhớ. Khi $W \le 10^4$ chạy rất nhanh; khi $W \ge 10^5$ (như suite `benchmark_stress`) DP có thể bị OOM.
- **DPUnbounded** dùng cùng bảng nhưng cho phép lấy một vật phẩm nhiều lần (truy hồi trên cùng dòng $i$).

#### `backtracking.py` — Quay lui
Duyệt cây nhị phân $2^n$ (chọn / không chọn từng vật phẩm), có cắt tỉa đơn giản: dừng nhánh nếu trọng lượng vượt quá $W$. Không có hàm chặn (upper bound function) nên chạy **chậm** trên tập lớn, dùng làm baseline để so sánh hiệu quả cắt tỉa.

#### `branch_and_bound.py` — Nhánh cận
Duyệt cây nhưng có thêm **hàm cận trên (upper bound function)**: ước lượng giá trị tối đa khả thi của nhánh bằng **LP relaxation** (greedy fractional trên các vật phẩm chưa quyết định). Nếu upper bound $\le$ best-so-far, thực hiện cắt nhánh lập tức.
- Các vật phẩm được sắp xếp theo mật độ trước khi duyệt để tối ưu hóa thứ tự nhánh DFS.
- Trên các instance benchmark $n=100$, BnB chạy chỉ mất $\sim 1\text{ms}$ trong khi DP mất $\sim 1\text{s}$ do BnB không phải duyệt và dựng toàn bộ bảng lớn.

---

### 2. `src/algorithms/simplex/` — Thuật toán Đơn hình

Đây là phần được cài đặt chi tiết trong project, gồm **5 solvers** xoay quanh phương pháp Đơn hình (Simplex) phục vụ giải LP relaxation và tìm nghiệm nguyên cho bài toán Cái túi 0/1.

#### Đưa về dạng LP chuẩn
Bài toán Knapsack LP relaxation được biểu diễn dưới dạng:

$$\max c^T x \quad \text{s.t.} \quad A x \leq b,\ x \geq 0$$

với:
- $c = (v_1, \dots, v_n)$ — vector giá trị.
- Ràng buộc đầu tiên của $A$: $(w_1, \dots, w_n) \le W$ (sức chứa).
- $n$ ràng buộc tiếp theo: $x_i \le 1$ (giới hạn mỗi vật phẩm chỉ lấy tối đa 1 phần).
- Tổng cộng: $m = n+1$ ràng buộc, $n$ biến quyết định, cộng thêm $m$ biến bù (slack variables) sau khi chuẩn hóa.

Hàm `_convert_to_lp_form()` trong `base_simplex.py` đảm nhận việc chuyển đổi này. Cơ chế lọc ràng buộc dư thừa `_filter_redundant_constraints()` giúp loại bỏ các ràng buộc trùng lặp, tối ưu hóa kích thước ma trận Tableau.

#### `primal_simplex.py` — Primal Simplex (Hai pha)
Cài đặt **Phương pháp Hai pha (Two-Phase Method)** chuẩn:
- **Pha I**: Thêm biến giả (artificial variables) để tìm điểm cơ sở khả thi ban đầu (BFS). Nếu giá trị tối ưu Pha I $> 0$, bài toán vô nghiệm khả thi (infeasible).
- **Pha II**: Khôi phục hàm mục tiêu gốc và tiến hành tối ưu hóa bằng các bước xoay Tableau (pivot).

Bảng Tableau được lưu dưới dạng `numpy.ndarray`, bước xoay được vectorized bằng `np.outer` để tránh các vòng lặp lồng nhau trong Python, tăng tốc độ xử lý vượt bậc.

#### `dual_simplex.py` — Dual Simplex
Hoạt động ngược chiều với Primal Simplex: xuất phát từ trạng thái đối ngẫu khả thi (dual-feasible) nhưng primal-infeasible (tồn tại các giá trị biên âm $b_i < 0$):
- **Bước 1**: Chọn hàng ra (leaving row) có giá trị biên âm nhất.
- **Bước 2**: Chọn cột vào (entering column) thông qua kiểm định tỷ lệ đối ngẫu (dual ratio test).
- **Ưu điểm**: Phù hợp tối ưu lại (re-optimization) cực nhanh khi thêm ràng buộc mới (như lát cắt Gomory hoặc chia nhánh BnB) mà không cần chạy lại Pha I từ đầu.

#### `branch_and_bound.py` (trong simplex/) — Simplex + Branch & Bound
Giải **0/1 Knapsack nguyên** bằng cách giải LP relaxation ở mỗi nút cây quyết định:
1. Giải LP relaxation bằng Primal Simplex thu được nghiệm $x^*$.
2. Nếu $x^*$ nguyên, cập nhật kỷ lục tốt nhất.
3. Nếu chứa giá trị fractional, chọn biến $x_j$ không nguyên để chia hai nhánh: $x_j = 0$ (thêm ràng buộc $x_j \le 0$) và $x_j = 1$ (thêm ràng buộc $x_j \ge 1$), tối ưu lại bằng Dual Simplex.

#### `gomory_cut.py` — Gomory Cutting Planes
Giải pháp tìm nghiệm nguyên bằng cách siết chặt đa diện khả thi mà không chia nhánh:
1. Giải LP relaxation thu được Tableau tối ưu chứa biến cơ sở fractional tại dòng $r$.
2. Sinh lát cắt Gomory:

$$\sum_{j \in \text{non-basic}} (a_{rj} - \lfloor a_{rj} \rfloor) x_j \geq (b_r - \lfloor b_r \rfloor)$$

3. Thêm ràng buộc cắt này vào Tableau và tối ưu lại bằng Dual Simplex. Lặp lại cho đến khi đạt nghiệm nguyên.

> [!WARNING]
> **Lưu ý về hiệu năng thực nghiệm của Simplex:**
> Bảng đo thời gian chạy thực tế dưới đây đo đạc trên môi trường chạy đơn nhân (single-core):
>
> | n | Greedy LP | PrimalSimplex | DualSimplex | Trạng thái kiểm thử |
> | :---: | :---: | :---: | :---: | :---: |
> | 100 | 0.05 ms | 5 ms | 5 ms | Khớp tuyệt đối (sai số < 1e-4) |
> | 200 | 0.1 ms | 21 ms | 24 ms | Khớp tuyệt đối |
> | 300 | 0.2 ms | 61 ms | 59 ms | Khớp tuyệt đối |
> | 500 | 0.3 ms | 421 ms | 416 ms | Khớp tuyệt đối |
> | 800 | 0.5 ms | 1.21 s | 1.15 s | Khớp tuyệt đối |
> | 1000 | 0.6 ms | 3.33 s | 3.38 s | Khớp tuyệt đối |
>
> Đường cong tăng trưởng thời gian chạy thực nghiệm tiệm cận sát mức $O(n^3)$.

---

## 📦 Các thư viện phụ thuộc

Dự án sử dụng các gói thư viện chuẩn trong khoa học dữ liệu:
- `numpy`
- `pandas`
- `matplotlib`
- `seaborn`
- `scipy`
- `tqdm`
- `flask`

Mọi thư viện đã được liệt kê chi tiết trong tệp [requirements.txt](requirements.txt).

---

## 👥 Tác giả

- **Nguyễn Hoàng Đạt**
- **Lê Sỹ Thức**
- **Nguyễn Hải Anh**

Dự án này là sản phẩm hợp tác phục vụ mục đích nghiên cứu — học tập về Operations Research và Combinatorial Optimization.
