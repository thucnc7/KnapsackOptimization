# 📊 Notebooks & Plotting Analytics - Phân tích & Đồ thị thống kê

Thư mục này chứa các công cụ hỗ trợ phân tích kết quả sau benchmark và tự động vẽ các đồ thị thống kê chất lượng cao phục vụ phân tích thực nghiệm.

---

## 🗺️ Điều hướng nhanh (Navigation)

- **Trang chủ dự án:** [README.md](../../README.md)
- **Mã nguồn tối ưu Python:** [KnapsackOptimization/README.md](../README.md)
  - 📊 [Phân tích & Đồ thị](README.md) - Thống kê và kiểm định thực nghiệm.
  - ⏱️ [Trình đo hiệu năng](../benchmark/README.md) - Hệ thống benchmark cô lập tiến trình.
  - ⚙️ [Quản lý dữ liệu](../data/README.md) - Sinh dữ liệu theo phân phối Gauss.
  - 🌐 [Giao diện Webapp](../webapp/README.md) - Bảng điều khiển Flask tương tác.

---

## 📂 Chi tiết các tệp tin

1. **`02_analysis_and_plots.ipynb`**:
   - Tệp Jupyter Notebook chính chứa các khối mã phân tích thống kê chuyên sâu.
   - Đọc dữ liệu đầu vào từ tệp CSV kết quả benchmark (mặc định tại `results/csv/benchmark_results.csv`).
   - Thực hiện phân tích phân tán (scatter), tìm kiếm/tối ưu khớp đường cong tiệm cận (curve fitting), so sánh bộ nhớ đỉnh (peak memory box-plots) và thời gian chạy thực nghiệm trung vị.

2. **`build_notebook.py`**:
   - Script sinh tự động toàn bộ nội dung mã nguồn của tệp Jupyter Notebook `02_analysis_and_plots.ipynb`.
   - Bạn không cần chỉnh sửa trực tiếp tệp `.ipynb`. Mọi thay đổi về thiết kế biểu đồ, cấu hình vẽ đồ thị nên được điều chỉnh tại tệp Python này, sau đó chạy `python notebooks/build_notebook.py` để biên dịch lại tệp Notebook.

3. **`execute_notebook.py`**:
   - **Script khuyến nghị để chạy nhanh:** Trích xuất toàn bộ các ô mã nguồn Python từ tệp Notebook `.ipynb` và thực thi trực tiếp trên chế độ dòng lệnh (headless execution).
   - Cho phép sinh lại toàn bộ ảnh đồ thị thống kê một cách nhanh chóng mà không yêu cầu bạn phải cài đặt hoặc khởi động giao diện Jupyter Notebook cồng kềnh.

---

## 🚀 Hướng dẫn thực thi

Hãy di chuyển vào thư mục gốc của bộ công cụ Python **`KnapsackOptimization/`** trước khi thực hiện các dòng lệnh dưới đây:

### Cách 1: Khởi chạy không cần giao diện (Khuyến nghị sử dụng)
Để tự động thực thi tất cả tính toán thống kê và cập nhật các tệp hình ảnh đồ thị mới nhất:
```bash
python notebooks/execute_notebook.py
```

> [!TIP]
> Khi chạy thành công, các đồ thị dạng PNG sắc nét (300 DPI) sẽ tự động được xuất ra thư mục `results/plots/` phục vụ việc phân tích trực quan.

### Cách 2: Chạy tương tác trên giao diện Jupyter
Nếu bạn muốn chỉnh sửa, tương tác hoặc kiểm tra trực tiếp các dòng mã phân tích:
1. Cài đặt thêm Jupyter hoặc tiện ích mở rộng Jupyter trên trình biên dịch code của bạn (ví dụ: VS Code Jupyter Extension).
2. Khởi chạy máy chủ Jupyter và mở tệp `notebooks/02_analysis_and_plots.ipynb`.
3. Chọn **Run All Cells** để thực thi toàn bộ tính toán và quan sát đồ thị trực quan.
