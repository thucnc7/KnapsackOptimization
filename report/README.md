# LaTeX report

Báo cáo "Ứng dụng các mô hình quy hoạch tuyến tính cho các loại bài toán Knapsack"
của Nguyễn Hoàng Đạt, Lê Sỹ Thức, Nguyễn Hải Anh.

## Compile

```bash
cd report
xelatex main.tex
xelatex main.tex   # second pass for ToC + references
```

Output: `main.pdf` (~19 pages).

## Các file local stubs (`*.sty`)

Một số package mà repo phụ thuộc **không có trong TeX Live basic** mặc định.
Để compile được standalone, repo bundle 4 stubs tối giản:

| File | Thay cho | Ghi chú |
|------|----------|---------|
| `husthesis-en.sty` | HUST official thesis class | Stub cover-page + layout cơ bản. Thay bằng file gốc nếu cần đúng format trường |
| `enumitem.sty` | `enumitem` package | Hỗ trợ `[noitemsep]`, `[leftmargin=*]` no-op |
| `algorithm2e.sty` | `algorithm2e` package | Stub các keyword + control flow + `\SetKwFunction` |
| `placeins.sty` | `placeins` package | `\FloatBarrier` → `\clearpage` |

Nếu hệ thống có sẵn các package này, LaTeX sẽ ưu tiên local stubs trong cùng
thư mục. Để dùng package gốc thay vì stub, chỉ cần xóa các file `.sty` trong
folder này.

## Placeholder images

Tất cả ảnh trong `image/` hiện là **placeholder PNG 400×300 px**. Để có ảnh
thật, cần generate qua các script trong repo (`data/quality.py`,
`notebooks/execute_notebook.py`, `notebooks/plot_sensitivity.py`).
