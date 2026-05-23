# 📊 Notebooks & Plotting Analytics

Thư mục này chứa các công cụ hỗ trợ phân tích kết quả sau benchmark và tự động vẽ các đồ thị thống kê chất lượng cao để chèn vào báo cáo thực nghiệm LaTeX.

---

## 📂 Chi tiết các tệp tin

1. **`02_analysis_and_plots.ipynb`**:
   * File Jupyter Notebook chính chứa các khối mã phân tích thống kê chuyên sâu.
   * Đọc dữ liệu đầu vào từ tệp CSV kết quả benchmark (mặc định tại `results/csv/benchmark_results.csv`).
   * Thực hiện phân tích phân tán (scatter), tối ưu khớp đường cong tiệm cận (curve fitting), so sánh bộ nhớ và thời gian chạy trung vị của các nhóm thuật toán.

2. **`build_notebook.py`**:
   * Script sinh tự động toàn bộ nội dung mã nguồn của file Jupyter Notebook `02_analysis_and_plots.ipynb`. 
   * Bạn không cần chỉnh sửa trực tiếp file Notebook `.ipynb`, mọi thay đổi về thiết kế biểu đồ, cấu hình vẽ đồ thị nên được điều chỉnh tại file Python này, sau đó chạy `python notebooks/build_notebook.py` để biên dịch lại file Notebook.

3. **`execute_notebook.py`**:
   * **Script khuyến nghị để chạy nhanh:** Trích xuất toàn bộ các ô mã nguồn Python từ tệp Notebook `.ipynb` và thực thi trực tiếp trên chế độ dòng lệnh (headless execution).
   * Cho phép sinh lại toàn bộ ảnh đồ thị thống kê một cách nhanh chóng mà không yêu cầu bạn phải cài đặt máy chủ Jupyter Notebook UI cồng kềnh.

---

## 🚀 Hướng dẫn thực thi

Hãy di chuyển vào thư mục gốc **`KnapsackOptimization/`** trước khi thực hiện các dòng lệnh dưới đây:

### Cách 1: Khởi chạy không cần giao diện (Khuyên Dùng)
Để tự động thực thi tất cả tính toán thống kê và cập nhật các tệp hình ảnh đồ thị mới nhất:
```bash
python notebooks/execute_notebook.py
```
> Khi chạy thành công, các đồ thị dạng PNG với mật độ điểm ảnh sắc nét (300 DPI) sẽ tự động được ghi đè vào thư mục `results/plots/` và đồng bộ sao chép trực tiếp sang thư mục `latex/image/` để báo cáo LaTeX của bạn được cập nhật ngay lập tức.

### Cách 2: Chạy thủ công trên giao diện Jupyter
Nếu bạn muốn tương tác trực tiếp với các dòng code phân tích:
1. Cài đặt thêm Jupyter hoặc cài đặt tiện ích mở rộng Jupyter trên VS Code.
2. Khởi chạy máy chủ Jupyter và mở tệp `notebooks/02_analysis_and_plots.ipynb`.
3. Nhấn **Run All Cells** để thực thi và quan sát biểu đồ hiển thị trực quan trực tiếp.
