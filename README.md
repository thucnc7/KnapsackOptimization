# 🎒 Knapsack Optimization - Bộ công cụ tối ưu thực nghiệm bài toán Cái túi

Thư mục này chứa toàn bộ mã nguồn cài đặt thuật toán, trình sinh testcase ngẫu nhiên có ràng buộc chất lượng cao, hệ thống chạy benchmark độc lập phòng ngừa lỗi, và các mã phân tích/vẽ đồ thị thống kê phục vụ báo cáo.

---

## 🚀 Hướng dẫn khởi chạy nhanh (Quick Start)

Hãy đảm bảo rằng bạn đã kích hoạt môi trường ảo (ví dụ: `.venv`) và cài đặt đầy đủ các thư viện trong `requirements.txt` trước khi chạy các lệnh sau:

### 1. Sinh dữ liệu mẫu (Testcases Generation)
Dữ liệu thử nghiệm được cấu hình chi tiết tại [data/test_scenarios.json](file:///e:/Antigravity%20Workspace/Knapsack/KnapsackOptimization/data/test_scenarios.json). Trình sinh dữ liệu sử dụng phương pháp **Gaussian jitter** (tự động biến thiên ngẫu nhiên xung quanh các neo kích thước phần tử $N$, tỷ lệ sức chứa `capacity_ratio`) và cơ chế **rejection sampling** để lọc các cặp trọng lượng - giá trị có hệ số tương quan Pearson mong muốn ($r \ge 0.9$ hoặc tùy chọn khác).
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
* `--timeout`: Thời gian chạy tối đa cho mỗi bài toán (mặc định: `60` giây, khuyến nghị `5` giây cho kiểm thử nhanh).
* `--limit`: Giới hạn số lượng testcase chạy thử (mặc định: `0` - chạy tất cả).
* `--raw`: Thư mục chứa dữ liệu đầu vào (mặc định: `data/raw`).
* `--output`: File lưu kết quả benchmark dạng CSV (mặc định: `results/csv/benchmark_results.csv`).

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

---

## 📂 Sơ đồ các mô-đun chính

* **`src/`**: Thư mục lõi chứa cài đặt các thuật toán:
  * Quy hoạch động (`DP.py`, `DPUnbounded.py`).
  * Nhánh cận (`BranchAndBound.py`).
  * Thuật toán tham lam (`Greedy01.py`, `GreedyFractional.py`).
  * Quy hoạch tuyến tính dựa trên Simplex (`SimplexBnB.py`, `PrimalSimplex.py`, `DualSimplex.py`, `GomoryCut.py`).
  * Quay lui (`Backtracking.py`).
* **`benchmark/`**: Chứa runner đo hiệu năng độc lập.
* **`data/`**: Sinh dữ liệu, lọc tương quan và kiểm tra chất lượng dữ liệu.
* **`notebooks/`**: Các script sinh và chạy notebook vẽ đồ thị phân tích tự động.
* **`results/`**: Thư mục đầu ra lưu trữ kết quả thống kê CSV và đồ thị PNG.
