# LaTeX Report — Final

Báo cáo cuối kỳ "Ứng dụng các mô hình quy hoạch tuyến tính cho các loại bài toán Knapsack"
của Nguyễn Hoàng Đạt, Lê Sỹ Thức, Nguyễn Hải Anh.

Nội dung và assets đầy đủ (template + ảnh + logo) lấy từ bản zip mà tác giả gửi.

## Compile

```bash
cd report
xelatex report.tex
bibtex report
xelatex report.tex
xelatex report.tex
```

Output: `report.pdf` — **47 trang, ~6 MB**.

## Bố cục

- `report.tex` — toàn bộ nội dung báo cáo (preamble + 7 sections + bibliography)
- `refs.bib` — references
- `husthesis-en.sty` — HUST official thesis template (do tác giả cung cấp trong zip)
- `image/` — 50+ ảnh thực nghiệm: quality, scatter, curvefit, sensitivity, memory comparison, runtime comparison
- `logo/` — HUST logo cho cover page

## Stubs cho TeX Live basic

Một số package mà repo phụ thuộc không có trong TeX Live basic. Repo bundle stubs tối giản:

| File | Thay cho | Vai trò |
|------|----------|---------|
| `vietnam.sty` | `vietnam` package | No-op (xelatex handle Unicode natively) |
| `nomencl.sty` | `nomencl` package | Stub `\nomname`, `\printnomenclature`, `\makenomenclature` |
| `multirow.sty` | `multirow` package | `\multirow{n}{w}{text}` → `text` |
| `enumitem.sty` | `enumitem` package | No-op `[noitemsep]`, `[leftmargin=*]` keys |
| `algorithm2e.sty` | `algorithm2e` package | Stub keywords + control flow + `\SetKwFunction` |
| `placeins.sty` | `placeins` package | `\FloatBarrier` → `\clearpage` |

Khi hệ thống có sẵn các package đầy đủ, xóa các file `.sty` tương ứng để LaTeX dùng package gốc.

## Patches xelatex-friendly

Bản tex gốc dùng `pdflatex` với `\usepackage[utf8]{vietnam}` và `\usepackage[vietnamese]{babel}`.
Để compile được với xelatex (Unicode native, font Vietnamese tốt hơn), preamble đã được patch:

- `\usepackage[utf8,nocaptions]{vietnam}` → `\usepackage{fontspec}` + `\usepackage{polyglossia}` + `\setdefaultlanguage{vietnamese}`
- `\usepackage[vietnamese]{babel}` → comment ra (polyglossia thay thế)
- `\usepackage{mathptmx}` → comment ra (xung đột Unicode tiếng Việt)

Nội dung body và 23 references không thay đổi.
