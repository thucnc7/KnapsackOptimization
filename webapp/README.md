# 🌐 Knapsack Optimization Visualizer - Giao diện trực quan hóa tương tác

Một webapp viết bằng Flask cung cấp bảng điều khiển (dashboard) trực quan và nhiều chế độ chạy để khám phá kết quả benchmark, kiểm thử trực tiếp các thuật toán giải bài toán Cái túi (Knapsack Problem) đã được cài đặt trong kho lưu trữ này.

---

## 🗺️ Điều hướng nhanh (Navigation)

- **Trang chủ dự án:** [README.md](../../README.md)
- **Mã nguồn tối ưu Python:** [KnapsackOptimization/README.md](../README.md)
  - 📊 [Phân tích & Đồ thị](../notebooks/README.md) - Thống kê và kiểm định thực nghiệm.
  - ⏱️ [Trình đo hiệu năng](../benchmark/README.md) - Hệ thống benchmark cô lập tiến trình.
  - ⚙️ [Quản lý dữ liệu](../data/README.md) - Sinh dữ liệu theo phân phối Gauss.
  - 🌐 [Giao diện Webapp](README.md) - Bảng điều khiển Flask tương tác.

---

## 🚀 Các chế độ chạy hỗ trợ (SPA Modes)

Giao diện SPA (Single Page Application) cung cấp **7 chế độ chạy** tương tác chính qua các thẻ tab điều khiển:

| Chế độ | Mô tả chi tiết chức năng |
| :--- | :--- |
| **Dashboard** | Tổng quan thống kê từ tệp kết quả CSV: tỷ lệ success/timeout/error, thời gian chạy và bộ nhớ trung bình, đồ thị phân phối thời gian theo kích thước $N$ (log scale), bảng chi tiết lọc theo thuật toán. |
| **So sánh** | Đối sánh cặp (paired comparison) giữa 2 thuật toán: biểu đồ scatter log-log về thời gian chạy, so khớp tính chính xác của giá trị tối ưu, biểu đồ tăng tốc (speedup) theo kích thước $N$. |
| **Single Solver** | Khởi chạy live 1 thuật toán đơn lẻ trên 1 testcase JSON có sẵn trong thư mục `data/raw/`. Hiển thị tiến trình chạy, biểu đồ phân tán các vật phẩm được chọn/không chọn, thanh đo dung lượng túi sử dụng. |
| **Multi-Solver** | Khởi chạy tuần tự nhiều thuật toán được chọn cùng lúc trên 1 testcase để so sánh realtime thời gian giải, bộ nhớ đỉnh và tính đúng đắn của kết quả tối ưu. |
| **Custom Instance** | Công cụ thiết lập thủ công: nhập trực tiếp dung lượng túi và danh sách vật phẩm tùy ý, hoặc tự động sinh ngẫu nhiên theo cấu hình đầu vào tùy chỉnh để thử nghiệm nhanh bất kỳ thuật toán nào. |
| **Data Quality** | Trực quan hóa cấu hình `test_scenarios.json` và hiển thị các biểu đồ phân tích chất lượng phân phối dữ liệu đã được xuất từ lệnh Python. |
| **Job Runner** | Giao diện điều khiển chạy nền các script hệ thống: `benchmark/runner.py`, `data/generator.py`, `data/quality.py` kèm theo cơ chế hiển thị log streaming realtime và thanh tiến trình (progress bar) được phân tích tự động từ thư viện `tqdm`. |

---

## 🛠️ Hướng dẫn cài đặt & Khởi chạy

### Bước 1: Cài đặt thư viện phụ thuộc
Đảm bảo bạn đã kích hoạt môi trường ảo `.venv` và cài đặt đầy đủ các gói thư viện:
```bash
pip install -r requirements.txt
```

### Bước 2: Khởi động Web Server
Chạy lệnh sau từ thư mục **`KnapsackOptimization/`**:
```bash
python -m webapp.app --port 5000 --debug
```

### Bước 3: Truy cập giao diện
Mở trình duyệt web của bạn và truy cập địa chỉ: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 📂 Sơ đồ kiến trúc Webapp

```text
webapp/
├── app.py                # Điểm khởi chạy Flask ứng dụng chính (entry point)
├── api/                  # Chứa các blueprint API
│   ├── benchmark_api.py  # Điểm cuối API thống kê CSV kết quả (/api/benchmark/*)
│   ├── data_api.py       # API quản lý testcase, kịch bản, thuật toán (/api/data/*)
│   ├── solver_api.py     # API gọi chạy trực tiếp live các thuật toán (/api/solver/*)
│   └── runner_api.py     # API quản lý điều khiển các tiến trình nền subprocess (/api/runner/*)
├── static/
│   ├── css/
│   │   └── main.css      # Cấu trúc giao diện và định dạng CSS
│   └── js/               # Mã nguồn xử lý JS chia thành các module tương ứng với các Panel
│       ├── utils.js      # Hàm tiện ích chung (định dạng, vẽ biểu đồ, AJAX)
│       ├── main.js       # Quản lý chuyển tab SPA (mode switcher)
│       ├── dashboard.js  # Logic bảng dashboard thống kê
│       ├── comparison.js # Logic so sánh cặp thuật toán
│       ├── solver.js     # Logic live solver đơn
│       ├── multi.js      # Logic live solver nhiều thuật toán song song
│       ├── custom.js     # Logic builder testcase tùy chỉnh
│       ├── quality.js    # Logic trực quan hóa chất lượng dữ liệu
│       └── runner.js     # Xử lý log streaming của Job Runner
└── templates/
    └── index.html        # Giao diện HTML trang đơn SPA dùng Bootstrap + CSS Grid
```

### Thiết kế Backend:
- Sử dụng **Flask** làm máy chủ API RESTful, định tuyến thông qua các Blueprint.
- Solver API gọi trực tiếp các lớp thuật toán trong `src/algorithms/` bằng cách tra cứu qua registry `benchmark.runner.get_algorithm_registry()`, tích hợp cơ chế đo bộ nhớ động thông qua thư viện `tracemalloc`.
- Runner API quản lý chạy nền các script hệ thống dưới dạng tiến trình con độc lập (`subprocess`), liên tục ghi file log tạm và trả kết quả live log streaming về phía client thông qua cơ chế polling định kỳ 2 giây.

### Thiết kế Frontend:
- Sử dụng mô hình Module Javascript thuần (Vanilla JS) kết hợp với thư viện vẽ biểu đồ **Chart.js v4** (nhập từ CDN), đảm bảo tải trang nhanh và không yêu cầu các bước đóng gói (build step) phức tạp.
- Các biểu đồ và logic điều khiển của từng panel được thiết kế theo cơ chế tải chậm (lazy initialization) — chỉ khởi tạo và nạp dữ liệu khi người dùng chuyển sang tab tương ứng, tối ưu hiệu năng bộ nhớ trình duyệt.

---

## 🔌 Đặc tả các điểm cuối API (API Endpoints)

| Phương thức | Điểm cuối (Endpoint) | Chức năng chi tiết |
| :---: | :--- | :--- |
| **GET** | `/api/benchmark/files` | Liệt kê các tệp CSV kết quả trong thư mục `results/csv/`. |
| **GET** | `/api/benchmark/raw` | Lọc dữ liệu thô từ CSV theo bộ lọc: `file`, `algorithm`, `status`, `limit`. |
| **GET** | `/api/benchmark/summary` | Lấy dữ liệu thống kê tổng hợp phân nhóm theo thuật toán và kích thước $N$. |
| **GET** | `/api/benchmark/compare` | So khớp kết quả và so sánh trực tiếp 2 thuật toán trên cùng tệp CSV. |
| **GET** | `/api/data/instances` | Liệt kê các tệp testcase JSON đang có trong thư mục dữ liệu kèm phân trang. |
| **GET** | `/api/data/instance/<id>` | Lấy nội dung chi tiết dạng JSON của một testcase cụ thể. |
| **GET** | `/api/data/scenarios` | Lấy nội dung cấu hình kịch bản hiện tại của `test_scenarios.json`. |
| **GET** | `/api/data/algorithms` | Trả về danh sách tên các thuật toán hiện đang khả dụng trong hệ thống. |
| **GET** | `/api/data/quality-images`| Liệt kê các biểu đồ chất lượng hiện có trong thư mục kết quả. |
| **POST** | `/api/solver/run` | Gửi yêu cầu giải trực tiếp testcase bằng 1 thuật toán chỉ định. |
| **POST** | `/api/solver/run-multi` | Gửi yêu cầu giải song song testcase bằng nhiều thuật toán chỉ định. |
| **POST** | `/api/runner/benchmark` | Kích hoạt chạy tiến trình benchmark `runner.py` trên nền hệ thống. |
| **POST** | `/api/runner/generator` | Kích hoạt chạy tiến trình sinh dữ liệu `generator.py` trên nền hệ thống. |
| **POST** | `/api/runner/quality` | Kích hoạt chạy đánh giá chất lượng `quality.py` trên nền hệ thống. |
| **GET** | `/api/runner/jobs` | Danh sách trạng thái các tiến trình chạy nền đang hoặc đã chạy. |
| **GET** | `/api/runner/jobs/<id>/log`| Đọc nội dung log thực thi realtime từ tiến trình nền. |
| **DELETE**| `/api/runner/jobs/<id>` | Cưỡng bức dừng (terminate) một tiến trình nền đang hoạt động. |

---

## ⚠️ Lưu ý khi sử dụng

> [!WARNING]
> - Một số thuật toán exact như Quy hoạch động (`DP`), Quay lui (`Backtracking`) và Quy hoạch nguyên đơn hình (`Branch & Bound Simplex`) sẽ chạy rất lâu và ngốn bộ nhớ trên các testcase lớn ($n \ge 1000$). Khi chạy trực tiếp trên các tab **Single Solver** hoặc **Multi-Solver**, các thuật toán này **không bị giới hạn thời gian tự động (timeout)** từ backend, dễ dẫn đến tình trạng treo tiến trình webapp. Hãy chọn testcase nhỏ hoặc vừa phải (ví dụ: $n \le 100$) khi sử dụng các giải thuật này, hoặc ưu tiên chọn các giải thuật tối ưu cao như `Greedy` và `BranchAndBound` (nhánh cận thường).
> - Tính năng chạy live và Custom Instance hiện tối ưu và hỗ trợ trực quan hóa tốt nhất cho bài toán Cái túi dạng 0/1.
