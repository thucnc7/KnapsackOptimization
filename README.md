# 🎒 Knapsack Optimization - Bộ công cụ tối ưu thực nghiệm bài toán Cái túi

Thư mục này chứa toàn bộ mã nguồn cài đặt thuật toán, trình sinh testcase ngẫu nhiên có ràng buộc chất lượng cao, hệ thống chạy benchmark độc lập phòng ngừa lỗi, mã phân tích/vẽ đồ thị thống kê phục vụ báo cáo, và **một webapp visualization tương tác** để khám phá kết quả benchmark cũng như chạy thử các thuật toán trực tiếp trong trình duyệt.

**Tác giả**: Nguyễn Hoàng Đạt · Lê Sỹ Thức · Nguyễn Hải Anh

---

## 🗂️ Giới thiệu cấu trúc repo

Repo được tổ chức theo nguyên tắc **tách biệt rõ ràng các lớp chức năng**: thuật toán (`src/`), sinh dữ liệu thực nghiệm (`data/`), khung benchmark (`benchmark/`), phân tích kết quả (`notebooks/`, `results/`), giao diện trực quan (`webapp/`), và tài liệu nghiên cứu (`plans/`). Mỗi lớp có thể chạy độc lập, đồng thời được liên kết qua một entry point thống nhất (`main.py`) và webapp.

| Thư mục | Vai trò | Khi nào cần đến |
|--------|---------|-----------------|
| **`src/`** | Cài đặt thuật toán: base classes + mixins, basic solvers (Greedy, DP, Backtracking, BnB), Simplex family (Primal, Dual, BnB+Simplex, Gomory) | Khi mở rộng/sửa thuật toán hoặc thêm solver mới |
| **`data/`** | Sinh test instances theo `test_scenarios.json` (Gaussian jitter + rejection sampling), kiểm tra chất lượng phân phối, output JSON instances | Khi muốn tạo dữ liệu thực nghiệm mới hoặc verify chất lượng dataset |
| **`benchmark/`** | Runner độc lập process-isolated với timeout + OOM protection, đo wall time + peak memory bằng `tracemalloc` | Khi chạy benchmark trên toàn bộ test suite, output CSV |
| **`webapp/`** | Flask + vanilla JS + Chart.js dashboard với 7 modes (xem mục 5 dưới), cho phép chạy live solver trong trình duyệt | Khi muốn khám phá kết quả tương tác, demo cho người khác xem |
| **`notebooks/`** | Sinh và execute Jupyter notebook tự động → xuất PNG (scatter, curve fitting, comparison plots) | Khi cần báo cáo định lượng dạng PDF/LaTeX với biểu đồ chất lượng publication |
| **`results/`** | Output: `csv/` (raw benchmark), `quality/` (phân tích dữ liệu), `plots/` (biểu đồ thực nghiệm) | Chứa artifacts của benchmark, không commit dữ liệu lớn vào git |
| **`plans/`** | Research reports về thuật toán (so sánh literature), implementation plans cho features mới | Khi nghiên cứu lý thuyết hoặc theo dõi quyết định thiết kế |
| **`main.py`** | Demo entry point: chạy 6 solvers trên 1 instance n=30, in bảng so sánh | Smoke test sau khi sửa code |

Sơ đồ chi tiết các file được liệt kê ở mục **Sơ đồ các mô-đun chính** bên dưới.

---

## 🚀 Hướng dẫn khởi chạy nhanh (Quick Start)

Hãy đảm bảo rằng bạn đã kích hoạt môi trường ảo (ví dụ: `.venv`) và cài đặt đầy đủ các thư viện trong `requirements.txt` trước khi chạy các lệnh sau:

```bash
pip install -r requirements.txt
```

### 1. Sinh dữ liệu mẫu (Testcases Generation)

Dữ liệu thử nghiệm được cấu hình chi tiết tại [`data/test_scenarios.json`](data/test_scenarios.json). Trình sinh dữ liệu sử dụng phương pháp **Gaussian jitter** (tự động biến thiên ngẫu nhiên xung quanh các neo kích thước phần tử $N$, tỷ lệ sức chứa `capacity_ratio`) và cơ chế **rejection sampling** để lọc các cặp trọng lượng - giá trị có hệ số tương quan Pearson mong muốn ($r \ge 0.9$ hoặc tùy chọn khác).

```bash
python data/generator.py
```
> Bộ dữ liệu raw sẽ được lưu vào thư mục `data/raw/` dưới định dạng JSON.

### 2. Kiểm tra chất lượng phân phối dữ liệu (Quality Check)

Để xác nhận xem dữ liệu sinh ra có tuân thủ phân phối chuẩn hình chuông Gauss quanh các giá trị neo và phân tán đồng đều hay không, hãy chạy script:

```bash
python data/quality.py --raw data/raw --output results/quality
```
> Biểu đồ phân phối Gauss và biểu đồ phân tán (scatter plot) sẽ được xuất ra thư mục `results/quality/`.

### 3. Thực thi Suite Benchmark hiệu năng

Chạy đo đạc thời gian thực thi (runtime) và lượng bộ nhớ tiêu thụ lớn nhất (peak memory) của từng thuật toán trên các testcase. Mỗi thuật toán được khởi chạy trên một tiến trình (process) độc lập để đảm bảo nếu xảy ra lỗi **TIMEOUT** hoặc **OOM** (hết bộ nhớ) ở một thuật toán, toàn bộ tiến trình benchmark vẫn tiếp tục hoàn thành bình thường.

```bash
python benchmark/runner.py --timeout 5 --output results/csv/benchmark_results.csv
```

**Các tham số chính:**
* `--timeout`: Thời gian chạy tối đa cho mỗi bài toán (mặc định: `5` giây).
* `--limit`: Giới hạn số lượng testcase chạy thử (`0` = chạy tất cả).
* `--raw`: Thư mục chứa dữ liệu đầu vào (mặc định: `data/raw`).
* `--output`: File lưu kết quả benchmark dạng CSV.

### 4. Tự động sinh báo cáo đồ thị (Analysis & Plotting)

Sau khi có tệp `benchmark_results.csv`, bạn có thể vẽ toàn bộ các biểu đồ phân tích thực nghiệm chỉ bằng một dòng lệnh duy nhất mà không cần cài đặt các ứng dụng Notebook UI nặng nề:

```bash
python notebooks/execute_notebook.py
```

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

Mở [http://127.0.0.1:5000](http://127.0.0.1:5000). Webapp cung cấp **7 chế độ chạy** trên cùng một giao diện SPA:

| Mode | Chức năng |
|------|-----------|
| **Dashboard** | Tổng quan CSV benchmark — success/timeout/error per algorithm, time/memory averages, thời gian theo N (log scale), bảng chi tiết |
| **So sánh** | Paired comparison 2 thuật toán bất kỳ — scatter log-log thời gian, value khớp/lệch, speedup theo N |
| **Single Solver** | Chọn 1 instance + 1 algorithm + timeout → chạy live với banner đếm thời gian + progress bar budget. Hiển thị capacity fill bar và scatter weight×value các items chọn/không chọn |
| **Multi-Solver** | Streaming NDJSON: chạy nhiều thuật toán tuần tự trên 1 instance, mỗi algo emit `tick` mỗi 250ms để UI cập nhật badge realtime |
| **Custom Instance** | Builder thủ công hoặc **sinh ngẫu nhiên** với config: N, max_weight, capacity_ratio, target Pearson r, seed |
| **Data Quality** | Hiển thị `test_scenarios.json` + các biểu đồ chất lượng đã generate |
| **Job Runner** | Spawn nền `benchmark/runner.py`, `data/generator.py`, `data/quality.py` với log streaming + progress bar parse từ tqdm |

Chi tiết xem [`webapp/README.md`](webapp/README.md).

---

## 📂 Sơ đồ các mô-đun chính

```
KnapsackOptimization/
├── src/                        Mã nguồn lõi
│   ├── models.py               Item, KnapsackInstance, metadata
│   └── algorithms/
│       ├── base.py             BaseSolver + ZeroOne/Fractional/Unbounded mixins
│       ├── basic/              Thuật toán cơ bản cho Knapsack
│       │   ├── greedy.py       Greedy01 (heuristic) + GreedyFractional (LP optimal)
│       │   ├── dp.py           Quy hoạch động (DP, DPUnbounded)
│       │   ├── backtracking.py Quay lui có cắt tỉa
│       │   └── branch_and_bound.py  Nhánh cận với LP relaxation bound
│       └── simplex/            LP solvers vectorized với numpy
│           ├── base_simplex.py        LP form conversion + dedup constraints
│           ├── primal_simplex.py      Two-Phase Primal Simplex
│           ├── dual_simplex.py        Dual Simplex (cho re-optimization)
│           ├── branch_and_bound.py    Simplex-based Branch & Bound (integer)
│           └── gomory_cut.py          Gomory cutting planes
│
├── benchmark/                  Benchmark runner độc lập
│   ├── runner.py               Process-isolated với timeout/OOM handling
│   └── metrics.py              tracemalloc + perf_counter wrapper
│
├── data/                       Sinh dữ liệu + kiểm tra chất lượng
│   ├── generator.py            Gaussian jitter + rejection sampling Pearson r
│   ├── quality.py              Phân tích phân phối, vẽ heatmap/dashboard
│   ├── test_scenarios.json     4 suite: core_exact, core_heuristic, stress, extreme_n
│   └── raw/                    JSON instances sinh ra
│
├── webapp/                     Flask + vanilla JS visualization SPA
│   ├── app.py                  Entry point
│   ├── api/                    4 blueprints: benchmark, data, solver, runner
│   ├── static/                 CSS + JS modules (Chart.js từ CDN)
│   └── templates/              SPA-style index.html với mode switcher
│
├── notebooks/                  Auto-generated analysis notebooks
│   ├── build_notebook.py       Sinh `.ipynb` từ template
│   └── execute_notebook.py     Run notebook → xuất PNG vào results/plots
│
├── results/                    Output: csv, plots, quality images
├── plans/                      Research reports & implementation plans
├── main.py                     Demo nhỏ chạy 6 solvers trên 1 instance n=30
└── requirements.txt
```

---

## 🧮 Các thuật toán

### Phát biểu bài toán

**0/1 Knapsack** (bài toán cái túi 0/1) — cho `n` vật phẩm, mỗi vật phẩm `i` có trọng lượng `w_i > 0` và giá trị `v_i > 0`, và một sức chứa `W`. Tìm tập con S các vật phẩm sao cho:

$$\max \sum_{i \in S} v_i \quad \text{subject to} \quad \sum_{i \in S} w_i \leq W$$

Tương đương dạng chương trình tuyến tính nguyên (Integer Linear Programming):

$$\max \sum_{i=1}^{n} v_i x_i \quad \text{s.t.} \quad \sum_{i=1}^{n} w_i x_i \leq W,\ x_i \in \{0, 1\}$$

**Fractional Knapsack** thay `x_i ∈ {0,1}` bằng `0 ≤ x_i ≤ 1`, cho phép lấy một phần vật phẩm. Đây chính là **LP relaxation** của bài 0/1.

**Unbounded Knapsack** thay bằng `x_i ∈ ℤ₊` — mỗi vật phẩm có thể lấy số lần không giới hạn.

### Bảng tổng quan

| Tên | Loại | Variant | Độ phức tạp | Optimality |
|-----|------|---------|-------------|------------|
| `GreedyKnapsackSolver` | Tham lam | 0/1 + Fractional | O(n log n) | ✓ cho Fractional, ✗ cho 0/1 |
| `DPKnapsackSolver` | Pseudo-polynomial | 0/1 + Unbounded | O(n·W) | ✓ |
| `BacktrackingSolver` | Vét cạn cắt tỉa | 0/1 | O(2ⁿ) worst case | ✓ |
| `BranchAndBoundSolver` | Nhánh cận + LP | 0/1 | O(2ⁿ) worst, ~polynomial mean | ✓ |
| `PrimalSimplexSolver` | Two-Phase Simplex | Fractional (LP) | exponential worst, ~O(n³) mean | ✓ |
| `DualSimplexSolver` | Dual Simplex | Fractional (LP) | exponential worst, ~O(n³) mean | ✓ |
| `BranchAndBoundSimplexSolver` | Simplex + BnB | 0/1 integer | exponential | ✓ |
| `GomoryCutSolver` | Cutting planes + Dual Simplex | 0/1 integer | có thể không hội tụ, polynomial cho LP-rank thấp | ✓ khi hội tụ |

---

### 1. `src/algorithms/basic/` — Thuật toán cơ bản

#### `greedy.py` — Tham lam (Greedy)

Sắp xếp vật phẩm giảm dần theo **mật độ giá trị** `v_i / w_i`, sau đó chọn lần lượt vật phẩm có mật độ cao nhất nếu còn vừa túi.

- **Fractional**: nếu vật phẩm cuối không vừa hết, lấy phần fractional cuối cho khít. Thuật toán này **tối ưu chứng minh được** cho LP relaxation (Dantzig 1957) — đây cũng chính là baseline ground-truth của project để verify các Simplex solvers.
- **0/1 Greedy**: dừng ngay khi vật phẩm tiếp theo không vừa. **Không tối ưu**, có thể sai rất xa (worst case approximation ratio = 1/2 nếu thêm trick "best single item").

Độ phức tạp `O(n log n)` (chỉ tốn ở sort). Trên `n=1000`: ~0.1ms.

#### `dp.py` — Quy hoạch động (Dynamic Programming)

Bảng `dp[i][w]` = giá trị tối đa khi xét i vật phẩm đầu và sức chứa w. Quan hệ truy hồi:

$$dp[i][w] = \max\left( dp[i-1][w],\ dp[i-1][w-w_i] + v_i \right)$$

- **Pseudo-polynomial**: `O(n·W)` thời gian và bộ nhớ. Khi `W ≤ 10⁴` là rất nhanh; khi `W ≥ 10⁵` (như suite `benchmark_stress`) DP có thể OOM.
- **DPUnbounded** dùng cùng bảng nhưng cho phép `dp[i-1] → dp[i]` (cùng dòng), enabling vật phẩm được lấy nhiều lần.

#### `backtracking.py` — Quay lui

Duyệt cây nhị phân `2ⁿ` (chọn / không chọn từng vật phẩm), với cắt tỉa: dừng nhánh nếu trọng lượng đã vượt `W`. Không có upper bound function nên **chậm** so với Branch & Bound, dùng làm baseline so sánh hiệu quả của cắt tỉa.

#### `branch_and_bound.py` — Nhánh cận

Giống Backtracking nhưng thêm **upper bound function**: tại mỗi nút, ước lượng best-case giá trị còn lại bằng **LP relaxation** (greedy fractional trên các vật phẩm chưa quyết định). Nếu upper bound ≤ best-so-far, cắt nhánh ngay.

- Sắp xếp items theo mật độ trước khi duyệt → DFS theo branching variable ordering tốt nhất.
- Trên các instance benchmark n=100, BnB chạy `~1ms` trong khi DP chạy `~1s` — vì BnB tận dụng được cấu trúc bài, DP thì phải build toàn bảng O(n·W).

---

### 2. `src/algorithms/simplex/` — Thuật toán Đơn hình ⭐

Đây là phần được implement chi tiết nhất trong project, với **5 solvers** xoay quanh phương pháp Đơn hình. Mục tiêu là giải LP relaxation và sau đó **dùng kết quả LP để tìm nghiệm nguyên** cho bài 0/1 Knapsack.

#### Dạng LP chuẩn

Knapsack LP relaxation được đưa về dạng:

$$\max c^T x \quad \text{s.t.} \quad A x \leq b,\ x \geq 0$$

với:
- `c = (v_1, ..., v_n)` — vector giá trị
- Hàng đầu của `A` là `(w_1, ..., w_n)` với `b_1 = W` (ràng buộc capacity)
- `n` hàng tiếp theo: `x_i ≤ 1` (upper bound mỗi vật phẩm)
- Tổng cộng: `m = n+1` constraints, `n` decision variables, plus `m` slack variables sau khi chuẩn hóa.

File `base_simplex.py` chứa hàm `_convert_to_lp_form()` thực hiện chuyển đổi này. Hàm `_filter_redundant_constraints()` loại bỏ ràng buộc trùng lặp (chỉ giữ RHS tighter nhất cho mỗi pattern hệ số) — **chú ý**: filter này được rewrite từ thuật toán Gauss O(n⁴) gốc sang dedup O(n·m) sau khi phát hiện filter Gauss tốn ~3-5 giờ chỉ để xác nhận điều hiển nhiên cho LP knapsack.

#### `primal_simplex.py` — Primal Simplex (Hai pha)

Implement **Phương pháp Hai pha (Two-Phase Method)** chuẩn, dùng khi xuất phát từ một LP có thể không có nghiệm khả thi ban đầu:

**Pha I** — Tìm điểm cơ sở khả thi (Basic Feasible Solution, BFS):
- Thêm **biến giả (artificial variables)** `a_i` cho mỗi ràng buộc có `b_i < 0`.
- Giải LP phụ: `min Σ a_i` (tương đương `max -Σ a_i`).
- Nếu giá trị tối ưu = 0, các biến giả bị đẩy ra khỏi cơ sở → BFS hợp lệ cho bài gốc. Nếu > 0, bài gốc **bất khả thi** (infeasible).

**Pha II** — Tối ưu từ BFS:
- Thay objective row bằng hàm mục tiêu gốc `max c^T x`.
- Phục hồi dạng chính tắc (canonical form) bằng cách trừ các hàng cơ sở.
- Iterate: chọn cột vào theo **Dantzig's rule** (entering variable = hệ số mục tiêu âm nhỏ nhất), chọn dòng ra theo **min ratio test**, pivot.

Cài đặt hiện tại dùng `numpy.ndarray` cho tableau, vectorize pivot bằng `np.outer(factors, pivot_row)` thay cho triple-nested Python loop. Trên `n=500`, một LP relaxation chạy ~0.4 giây (trước khi vectorize: dự kiến ~5 giờ vì filter Gauss + Python loop).

#### `dual_simplex.py` — Dual Simplex

**Khác biệt cốt lõi**: Dual Simplex bắt đầu từ một tableau **dual-feasible nhưng primal-infeasible** (đối ngẫu khả thi nhưng primal không khả thi — tức `b_i < 0` ở một số dòng). Ngược chiều Primal:
- **Chọn dòng ra (leaving row) trước**: dòng có `b_i` âm nhất.
- **Chọn cột vào (entering column) sau**: theo dual ratio test trên hàng đó.

Tại sao quan trọng?
- **Re-optimization sau khi thêm ràng buộc**: Sau khi thêm một cut (như Gomory), tableau cũ vẫn dual-feasible (objective row không đổi) nhưng có thể primal-infeasible (RHS âm). Dual Simplex re-optimize **không cần build lại từ đầu**.
- **Sensitivity analysis**: Khi RHS thay đổi nhỏ, Dual Simplex là tool chuẩn để khôi phục optimality.

File còn export `add_constraint()`, `update_rhs()`, `update_objective()` để hỗ trợ re-optimization, được Gomory Cut và Branch & Bound + Simplex sử dụng.

#### `branch_and_bound.py` (trong simplex/) — Simplex + Branch & Bound

Giải **0/1 Knapsack nguyên** bằng cách dùng LP relaxation làm hàm cận trên:

1. Giải LP relaxation bằng Primal Simplex → được nghiệm `x*` (có thể fractional).
2. Nếu `x*` đã nguyên → done.
3. Nếu không, chọn một biến `x_j ∈ (0, 1)` để branching, tạo 2 nhánh:
   - **Nhánh 0**: thêm ràng buộc `x_j = 0`, re-optimize bằng Dual Simplex.
   - **Nhánh 1**: thêm ràng buộc `x_j = 1`, re-optimize.
4. Cắt nhánh nếu LP bound ≤ best integer solution đã tìm.

Khác `basic/branch_and_bound.py` ở chỗ: bản này dùng **Simplex** để tính bound (chính xác hơn về mặt LP theory), trong khi bản basic dùng greedy fractional. Trade-off: chính xác hơn nhưng chậm hơn vì mỗi nhánh phải re-optimize.

#### `gomory_cut.py` — Gomory Cutting Planes

Một phương pháp khác để tìm nghiệm nguyên từ LP relaxation, **không dùng branching**:

1. Giải LP relaxation, được tableau optimal với một số biến cơ sở fractional.
2. Chọn dòng `r` có biến cơ sở fractional (gọi giá trị là `b̄_r`).
3. Sinh ra **Gomory cut**:

   $$\sum_{j \in \text{non-basic}} \{ \bar{a}_{rj} \} x_j \geq \{ \bar{b}_r \}$$

   với `{x}` là phần thập phân của x. Cut này **không loại bỏ nghiệm nguyên hợp lệ nào** nhưng cắt được nghiệm fractional hiện tại.
4. Thêm cut vào tableau và re-optimize bằng Dual Simplex.
5. Lặp đến khi tất cả biến cơ sở nguyên (hoặc declare numerical failure).

Lý thuyết Gomory đảm bảo hữu hạn iterations cho integer programs với LP có rank cố định. Trong thực tế, hội tụ phụ thuộc nhiều vào numerical precision — vì vậy implementation có epsilon cleanup ở mỗi pivot.

#### Tại sao dùng Simplex cho bài đơn giản như Knapsack?

Câu hỏi hợp lý vì Greedy fractional đã giải LP relaxation trong `O(n log n)`. Có 3 lý do để vẫn cài đặt:

1. **Giáo dục**: Simplex là method nền tảng của Operations Research. Cài đặt từ con số 0 trên bài knapsack (LP đơn giản, có nghiệm phân tích để verify) là bài tập học thuật chuẩn.
2. **Cầu nối sang Integer Programming**: Một khi có Simplex + Dual Simplex, ta có thể implement Branch & Bound (với simplex bound), Gomory cuts, Lagrangian relaxation, column generation... Tất cả đều cần Simplex hoặc Dual Simplex làm primitive.
3. **Benchmark research**: Đo wall-time của pure Python + NumPy Simplex trên dải `n=100..1000` là **chỗ trống trong literature** — commercial solvers (CPLEX, Gurobi) báo cáo "<1ms" (không thú vị), benchmark papers focus ở `n > 10⁴`. Project này lấp khoảng trống đó. Xem chi tiết tại [`plans/reports/simplex-knapsack-lp-benchmarks-research.md`](plans/reports/simplex-knapsack-lp-benchmarks-research.md) và [`plans/reports/simplex-runtime-benchmarks-research.md`](plans/reports/simplex-runtime-benchmarks-research.md).

#### Đo lường hiệu năng Simplex (verified)

Trên LP relaxation knapsack với items sinh ngẫu nhiên, đo wall-time end-to-end (Two-Phase, single core, MacBook Apple Silicon, Python 3.11 + NumPy):

| n | Greedy LP | PrimalSimplex | DualSimplex | Verify khớp |
|---|----------:|--------------:|------------:|:-----------:|
| 100 | 0.05 ms | 5 ms | 5 ms | ✓ |
| 200 | 0.1 ms | 21 ms | 24 ms | ✓ |
| 300 | 0.2 ms | 61 ms | 59 ms | ✓ |
| 500 | 0.3 ms | 421 ms | 416 ms | ✓ |
| 800 | 0.5 ms | 1.21 s | 1.15 s | ✓ |
| 1000 | 0.6 ms | 3.33 s | 3.38 s | ✓ |

Tất cả khớp tuyệt đối với Greedy LP (relative error < 1e-4). Scaling thực nghiệm rất gần `O(n³)`, đúng với kỳ vọng dense-tableau Simplex (số pivot ~O(n), chi phí mỗi pivot ~O(n²) khi dùng numpy vectorize).

---

## 📦 Phụ thuộc

```
numpy
pandas
matplotlib
seaborn
scipy
tqdm
flask
```

Tất cả đã được liệt kê trong `requirements.txt`.

---

## 👥 Tác giả

- **Nguyễn Hoàng Đạt**
- **Lê Sỹ Thức**
- **Nguyễn Hải Anh**

Project này là sản phẩm hợp tác phục vụ mục đích nghiên cứu — học tập về Operations Research và Combinatorial Optimization.
