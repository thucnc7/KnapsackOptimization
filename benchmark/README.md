# ⏱️ Benchmark Runner Suite

Thư mục này chứa bộ công cụ chạy đo đạc (benchmark) hiệu năng của các thuật toán một cách độc lập và an toàn. 

Để ngăn chặn các trường hợp thuật toán rơi vào vòng lặp vô hạn (gây đứng máy) hoặc ngốn sạch RAM hệ thống (gây sập chương trình), **mỗi thuật toán được khởi chạy và theo dõi trong một tiến trình (process) riêng biệt**. Nhờ cơ chế cách ly này, nếu một thuật toán bị **TIMEOUT** (quá thời gian) hoặc **OOM** (Out of Memory - tràn bộ nhớ), tiến trình đó sẽ bị chấm dứt và suite benchmark vẫn an toàn tiếp tục chạy các bài test tiếp theo.

---

## 🚀 Hướng dẫn khởi chạy nhanh

Hãy di chuyển vào thư mục gốc của bộ công cụ Python **`KnapsackOptimization/`** trước khi thực hiện các dòng lệnh sau:

### Lệnh chạy mặc định (Timeout 60s, chạy toàn bộ instance):
```bash
python benchmark/runner.py
```

### Lệnh kiểm thử nhanh (Timeout 5 giây, giới hạn chỉ chạy 10 instance mẫu):
```bash
python benchmark/runner.py --limit 10 --timeout 5
```

### Lệnh chạy chính thức để xuất file kết quả phân tích:
```bash
python benchmark/runner.py --timeout 5 --output results/csv/benchmark_results.csv
```

---

## 🛠️ Danh sách các tùy chọn dòng lệnh (CLI Parameters)

Khi gọi chạy `python benchmark/runner.py`, bạn có thể truyền thêm các tham số tùy chọn sau:

| Tham số | Giá trị mặc định | Ý nghĩa |
| :--- | :--- | :--- |
| `--raw` | `data/raw` | Thư mục chứa các tệp testcase JSON đầu vào. |
| `--output` | `results/csv/benchmark_results.csv` | Đường dẫn tệp CSV đầu ra để lưu kết quả. |
| `--timeout` | `60` | Thời gian chạy tối đa cho mỗi lượt giải của một thuật toán (tính bằng giây). |
| `--limit` | `0` | Giới hạn số lượng testcase chạy thực tế (`0` tương ứng chạy toàn bộ dữ liệu có trong thư mục `--raw`). |

---

## 📊 Mô tả định dạng đầu ra (CSV Columns)

Tệp CSV kết quả benchmark xuất ra chứa các cột thông tin sau để phục vụ phân tích:

* **`test_id`**: Định danh duy nhất của bộ dữ liệu testcase.
* **`algorithm`**: Tên thuật toán được thử nghiệm (ví dụ: `DP`, `BranchAndBound`, `Greedy01`,...).
* **`knapsack_type`**: Loại bài toán Knapsack (`0/1`, `fractional`, `unbounded`).
* **`status`**: Trạng thái thực thi của thuật toán (Xem chi tiết bên dưới).
* **`time_sec`**: Thời gian chạy thực tế của thuật toán (tính bằng giây).
* **`peak_memory_mb`**: Lượng bộ nhớ RAM lớn nhất thuật toán sử dụng trong quá trình giải quyết (tính bằng MB).
* **`optimal_value`**: Giá trị tối ưu tìm được (đối với thuật toán chính xác) hoặc giá trị xấp xỉ gần đúng (đối với thuật toán tham lam/heuristic).
* **`n`**: Số lượng phần tử trong túi của testcase đó.
* **`capacity`**: Sức chứa tối đa của cái túi.
* **`capacity_to_weight_ratio`**: Tỷ lệ sức chứa chia cho tổng trọng lượng của tất cả phần tử trong testcase.
* **`pearson_corr`**: Hệ số tương quan Pearson giữa Trọng lượng và Giá trị của các phần tử trong testcase.
* **`density_variance`**: Độ lệch chuẩn mật độ giá trị/trọng lượng của testcase.

---

## ⚠️ Giải thích các mã trạng thái (`status`)

Kết quả thực thi của mỗi thuật toán được phân loại thành một trong các trạng thái sau:

1. **`SUCCESS`**: Thuật toán chạy thành công, tìm ra kết quả tối ưu trong thời gian và bộ nhớ cho phép.
2. **`TIMEOUT`**: Thuật toán vượt quá giới hạn thời gian chạy cho phép (đặt bởi tham số `--timeout`). Tiến trình bị cưỡng bức tắt.
3. **`OOM` (Out of Memory)**: Thuật toán vượt quá dung lượng RAM hệ thống hoặc bị tràn bộ nhớ trong quá trình tính toán. Tiến trình bị cưỡng bức tắt để bảo vệ máy chủ thực nghiệm.
4. **`ERROR`**: Thuật toán gặp lỗi biệt lệ lập trình khác (Runtime Exception, lỗi logic nội bộ,...).
