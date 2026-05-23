# 📝 Báo cáo thực nghiệm & Slide thuyết trình LaTeX

Thư mục này chứa báo cáo khoa học chính thức và slide thuyết trình (Beamer) của dự án:
**"Ứng dụng các mô hình quy hoạch tuyến tính cho các loại bài toán Knapsack"**
Thực hiện bởi: Nguyễn Hoàng Đạt · Lê Sỹ Thức · Nguyễn Hải Anh.

---

## 🗺️ Điều hướng nhanh (Navigation)

- **Trang chủ dự án:** [README.md](../../README.md)
- **Mã nguồn tối ưu Python:** [KnapsackOptimization/README.md](../README.md)
  - 📊 [Phân tích & Đồ thị](../notebooks/README.md) - Thống kê và kiểm định thực nghiệm.
  - ⏱️ [Trình đo hiệu năng](../benchmark/README.md) - Hệ thống benchmark cô lập tiến trình.
  - ⚙️ [Quản lý dữ liệu](../data/README.md) - Sinh dữ liệu theo phân phối Gauss.
  - 🌐 [Giao diện Webapp](../webapp/README.md) - Bảng điều khiển Flask tương tác.
  - 📝 [Báo cáo LaTeX](README.md) - Báo cáo thực nghiệm khoa học chi tiết.

---

## 📂 Danh sách tệp tin

- **`report.tex`** — Mã nguồn LaTeX của báo cáo chính (preamble + 7 chương + danh mục tham khảo).
- **`report.pdf`** — Bản báo cáo PDF hoàn chỉnh đã được biên dịch (~49 trang).
- **`slides.tex`** — Mã nguồn LaTeX của slide thuyết trình Beamer (thời lượng khoảng 15 phút).
- **`slides.pdf`** — Bản slide PDF hoàn chỉnh phục vụ báo cáo thuyết trình.
- **`refs.bib`** — Danh mục tài liệu tham khảo chuẩn BibTeX (chứa trích dẫn thuật toán LP, NP-hard, Simplex...).
- **`husthesis-en.sty`** — Tệp cấu hình giao diện luận văn chuẩn chính thức.
- **`image/`** — Thư mục chứa các đồ thị phân tích thực nghiệm (quality check, curve fitting, benchmark comparison, sensitivity analysis).
- **`logo/`** — Thư mục chứa các ảnh logo trường phục vụ trang bìa báo cáo.

---

## 🚀 Hướng dẫn biên dịch (Compile Guide)

Hệ thống được đồng bộ hóa và biên dịch tối ưu nhất bằng **pdfLaTeX**. Đảm bảo máy tính của bạn đã cài đặt một phân phối LaTeX đầy đủ (như MiKTeX hoặc TeX Live).

### 1. Biên dịch báo cáo chính (`report.tex`):
Di chuyển vào thư mục `report/` và thực thi:
```bash
pdflatex report.tex
bibtex report.aux
pdflatex report.tex
pdflatex report.tex
```

### 2. Biên dịch slide thuyết trình Beamer (`slides.tex`):
```bash
pdflatex slides.tex
pdflatex slides.tex
```

> [!TIP]
> **Đồng bộ hóa đồ thị:** Khi bạn chạy lại pipeline phân tích thực nghiệm thông qua lệnh `python notebooks/execute_notebook.py` từ thư mục gốc, các hình ảnh đồ thị mới nhất sẽ tự động được sao chép và cập nhật trực tiếp vào thư mục `report/image/` để phục vụ việc biên dịch báo cáo tức thời.
