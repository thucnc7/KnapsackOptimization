# 🎒 Knapsack Optimization - Bộ công cụ tối ưu thực nghiệm bài toán Cái túi

Thư mục này chứa toàn bộ mã nguồn cài đặt thuật toán, trình sinh testcase ngẫu nhiên có ràng buộc chất lượng cao, hệ thống chạy benchmark độc lập phòng ngừa lỗi, mã phân tích/vẽ đồ thị thống kê phục vụ báo cáo, và **một webapp visualization tương tác** để khám phá kết quả benchmark cũng như chạy thử các thuật toán trực tiếp trong trình duyệt.

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

## 🧮 Danh sách thuật toán

| Tên | Loại | Knapsack variant | Mô tả |
|-----|------|------------------|-------|
| `DPKnapsackSolver` | Exact | 0/1, Unbounded | Quy hoạch động O(n·W) |
| `BranchAndBoundSolver` | Exact | 0/1 | Nhánh cận với LP relaxation upper bound |
| `BacktrackingSolver` | Exact | 0/1 | Vét cạn có cắt tỉa |
| `GreedyKnapsackSolver` | Heuristic (0/1) / Exact (fractional) | 0/1, Fractional | Sort theo v/w density |
| `PrimalSimplexSolver` | Exact LP | Fractional | Two-Phase Method, vectorized numpy |
| `DualSimplexSolver` | Exact LP | Fractional | Dual Simplex, vectorized numpy |
| `BranchAndBoundSimplexSolver` | Exact | 0/1 (integer) | Simplex + BnB cho integer programming |
| `GomoryCutSolver` | Exact | 0/1 (integer) | Cutting planes Gomory + Dual Simplex |

**Lưu ý về hiệu năng Simplex**: Tableau được lưu dưới dạng `numpy.ndarray`; mỗi pivot dùng `np.outer` thay cho triple-nested Python loop. Trên dải `n=100..1000` cho LP relaxation, runtime đo được là 5ms → 3.3s (curve gần `O(n³)`, đúng với kỳ vọng dense-tableau pure Python + numpy). Xem thêm [`plans/reports/simplex-knapsack-lp-benchmarks-research.md`](plans/reports/simplex-knapsack-lp-benchmarks-research.md) để so sánh với các paper/solver khác.

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
