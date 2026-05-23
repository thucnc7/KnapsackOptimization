# ⏱️ Benchmark Runner Suite - Đo đạc hiệu năng thuật toán

Thư mục này chứa bộ công cụ chạy đo đạc (benchmark) hiệu năng của các thuật toán một cách độc lập, an toàn và chính xác. 

Để ngăn chặn các trường hợp thuật toán rơi vào vòng lặp vô hạn (gây đứng máy) hoặc ngốn sạch RAM hệ thống (gây sập chương trình), **mỗi thuật toán được khởi chạy và theo dõi trong một tiến trình (process) độc lập**. Nhờ cơ chế cách ly này, nếu một thuật toán bị **TIMEOUT** (quá thời gian) hoặc **OOM** (Out of Memory - tràn bộ nhớ), tiến trình đó sẽ bị chấm dứt và suite benchmark vẫn an toàn tiếp tục chạy các bài test tiếp theo.

---

## 🗺️ Điều hướng nhanh (Navigation)

- **Trang chủ dự án:** [README.md](../../README.md)
- **Mã nguồn tối ưu Python:** [KnapsackOptimization/README.md](../README.md)
  - 📊 [Phân tích & Đồ thị](../notebooks/README.md) - Thống kê và kiểm định thực nghiệm.
  - ⏱️ [Trình đo hiệu năng](README.md) - Hệ thống benchmark cô lập tiến trình.
  - ⚙️ [Quản lý dữ liệu](../data/README.md) - Sinh dữ liệu theo phân phối Gauss.
  - 🌐 [Giao diện Webapp](../webapp/README.md) - Bảng điều khiển Flask tương tác.

---

## 🚀 Hướng dẫn khởi chạy nhanh

Hãy di chuyển vào thư mục gốc của bộ công cụ Python **`KnapsackOptimization/`** trước khi thực hiện các dòng lệnh sau:

### 1. Lệnh chạy mặc định (Timeout 60s, chạy toàn bộ instance):
```bash
python benchmark/runner.py
```

### 2. Lệnh kiểm thử nhanh (Timeout 5 giây, giới hạn chỉ chạy 10 instance mẫu):
```bash
python benchmark/runner.py --limit 10 --timeout 5
```

### 3. Lệnh chạy chính thức để xuất file kết quả phân tích:
```bash
python benchmark/runner.py --timeout 5 --output results/csv/benchmark_results.csv
```

---

## 🛠️ Danh sách các tùy chọn dòng lệnh (CLI Parameters)

Khi gọi chạy `python benchmark/runner.py`, bạn có thể truyền thêm các tham số tùy chọn sau:

| Tham số | Giá trị mặc định | Ý nghĩa |
| :--- | :---: | :--- |
| `--raw` | `data/raw` | Thư mục chứa các tệp testcase JSON đầu vào. |
| `--output` | `results/csv/benchmark_results.csv` | Đường dẫn tệp CSV đầu ra để lưu kết quả. |
| `--timeout` | `60` | Thời gian chạy tối đa cho mỗi lượt giải của một thuật toán (tính bằng giây). |
| `--limit` | `0` | Giới hạn số lượng testcase chạy thực tế (`0` tương ứng chạy toàn bộ dữ liệu có trong thư mục `--raw`). |

---

## 📊 Mô tả định dạng đầu ra (CSV Columns)

Tệp CSV kết quả benchmark xuất ra chứa các cột thông tin sau để phục vụ việc phân tích đồ thị:

| Tên cột | Định dạng | Mô tả thông tin |
| :--- | :---: | :--- |
| `test_id` | Chuỗi ký tự | Định danh duy nhất của bộ dữ liệu testcase. |
| `algorithm` | Chuỗi ký tự | Tên thuật toán được thử nghiệm (ví dụ: `DP`, `BranchAndBound`, `Greedy01`,...). |
| `knapsack_type` | Chuỗi ký tự | Loại bài toán Knapsack (`0/1`, `fractional`, `unbounded`). |
| `status` | Khóa trạng thái | Trạng thái thực thi của thuật toán (Xem chi tiết bảng dưới). |
| `time_sec` | Số thực | Thời gian chạy thực tế của thuật toán (tính bằng giây). |
| `peak_memory_mb` | Số thực | Lượng bộ nhớ RAM lớn nhất thuật toán sử dụng trong quá trình giải quyết (tính bằng MB). |
| `optimal_value` | Số thực | Giá trị tối ưu tìm được (đối với thuật toán chính xác) hoặc giá trị xấp xỉ gần đúng (đối với thuật toán tham lam/heuristic). |
| `n` | Số nguyên | Số lượng vật phẩm thực tế trong testcase. |
| `capacity` | Số thực | Sức chứa tối đa của cái túi. |
| `capacity_to_weight_ratio` | Số thực | Tỷ lệ sức chứa chia cho tổng trọng lượng của tất cả phần tử trong testcase. |
| `pearson_corr` | Số thực | Hệ số tương quan Pearson giữa Trọng lượng và Giá trị của các phần tử trong testcase. |
| `density_variance` | Số thực | Độ lệch chuẩn mật độ giá trị/trọng lượng của testcase. |

---

## ⚠️ Giải thích các mã trạng thái (`status`)

Kết quả thực thi của mỗi thuật toán được phân loại thành một trong các trạng thái sau để vẽ biểu đồ so sánh:

| Trạng thái | Mô tả chi tiết | Hành động hệ thống |
| :---: | :--- | :--- |
| **`SUCCESS`** | Thuật toán chạy thành công, tìm ra kết quả tối ưu trong thời gian và bộ nhớ cho phép. | Lưu kết quả và tiếp tục. |
| **`TIMEOUT`** | Thuật toán vượt quá giới hạn thời gian chạy cho phép (đặt bởi tham số `--timeout`). | Tiến trình bị cưỡng bức tắt, ghi trạng thái quá giờ. |
| **`OOM`** | Thuật toán vượt quá dung lượng RAM hệ thống hoặc bị tràn bộ nhớ trong quá trình tính toán. | Tiến trình bị cưỡng bức tắt để bảo vệ máy chủ thực nghiệm. |
| **`ERROR`** | Thuật toán gặp lỗi ngoại lệ lập trình khác (Runtime Exception, lỗi logic nội bộ,...). | Lưu dấu vết lỗi (stack trace) phục vụ sửa lỗi. |

> [!IMPORTANT]
> Bộ benchmark sử dụng thư viện `multiprocessing` để tạo các tiến trình con cách ly độc lập. Việc đo đạc dung lượng bộ nhớ đỉnh sử dụng phương pháp thăm dò luồng chạy thông qua thư viện `tracemalloc` cho mỗi tiến trình.
