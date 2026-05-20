# Data Management Component

Thư mục này quản lý cấu hình và tự động sinh tập dữ liệu thử nghiệm (Benchmark Datasets)
cho bài toán Ba lô 0/1. Hệ thống chạy theo cơ chế **config-driven**, tách biệt hoàn toàn
giữa tham số kịch bản và mã nguồn sinh dữ liệu.

---

## 1. Cấu hình kịch bản (`test_scenarios.json`)

File `data/test_scenarios.json` lưu một mảng các kịch bản. Bạn có thể thay đổi các tham
số để điều khiển số lượng và tính chất dữ liệu đầu ra.

Ví dụ cấu hình:

```json
[
  {
    "name": "benchmark_core",
    "description": "Bo testcase chuan de so sanh cong bang giua fractional va 0/1 (n, capacity_ratio, pearson_r).",
    "n_values": [10, 50, 100, 500],
    "max_weight": 1000,
    "capacity_ratios": [0.1, 0.5, 0.9],
    "pearson_r_targets": [0.0, 0.5, 0.95],
    "instances_per_config": 5
  }
]
```

Ý nghĩa tham số:

| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `name` | ✅ | Tên kịch bản (dùng làm tiền tố đặt tên file). |
| `description` | ❌ | Mô tả mục đích kịch bản. |
| `n_values` | ✅ | Danh sách số lượng vật phẩm cần sinh. |
| `max_weight` | ❌ | Khối lượng tối đa mỗi vật phẩm (mặc định `1000`). |
| `capacity_ratios` | ✅ | Tỷ lệ sức chứa W so với tổng khối lượng `sum(w_i)`. |
| `pearson_r_targets` | ✅ | Danh sách hệ số tương quan Pearson mục tiêu giữa `weight` và `value`. Giá trị trong `[-1.0, 1.0]`. |
| `instances_per_config` | ✅ | Số file sinh ra cho mỗi tổ hợp tham số. |

> **Ghi chú về `pearson_r_targets`:**
> - `0.0` → Hoàn toàn ngẫu nhiên (uncorrelated) — bài toán trung bình.
> - `0.5` → Tương quan vừa phải (weakly correlated).
> - `0.95` → Tương quan cao (strongly correlated) — làm suy yếu khả năng cắt nhánh của Branch & Bound.

---

## 2. Thực thi sinh dữ liệu (`generator.py`)

Sau khi cấu hình kịch bản, chạy lệnh từ thư mục gốc của dự án:

```bash
# Chạy với seed mặc định (42)
python data/generator.py

# Chạy với seed tuỳ chọn
python data/generator.py --seed 123

# Chạy với file config khác
python data/generator.py --config path/to/config.json --seed 42
```

Tham số CLI:

| Tham số | Mặc định | Mô tả |
|---|---|---|
| `--config` | `data/test_scenarios.json` | Đường dẫn file cấu hình kịch bản. |
| `--seed` | `42` | Seed ngẫu nhiên, đảm bảo kết quả tái tạo được (reproducible). |

> **Lưu ý:** Cùng `--seed` sẽ luôn sinh ra **đúng bộ dữ liệu giống nhau**.
> Mỗi testcase còn lưu `instance_seed` để tái tạo từng file riêng lẻ.

**Thuật toán sinh dữ liệu:**  
Generator dùng phương pháp **Cholesky / linear combination** để kiểm soát Pearson r:
- Sinh hai biến chuẩn độc lập `x`, `z ~ N(0,1)`.
- Tạo `y = r·x + √(1-r²)·z` — có tương quan đúng `r` với `x`.
- Scale cả hai về `[1, max_weight]` và làm tròn thành số nguyên.

---

## 3. Định dạng dữ liệu đầu ra (`data/raw/`)

Mỗi file đại diện cho một bài toán cụ thể, đặt tên theo quy ước:

```
{scenario_name}_n{n}_wmax{max_weight}_cr{capacity_ratio}_pr{pearson_r}_{index}.json
```

Ví dụ: `algorithmic_scaling_test_n100_wmax1000_cr0.5_pr0.95_03.json`

Ví dụ nội dung JSON:

```json
{
  "test_id": "benchmark_core_n10_wmax1000_cr0.5_pr0_01",
  "capacity": 1772.5,
  "metadata": {
    "n": 10,
    "capacity_ratio": 0.5,
    "pearson_r": 0.147,
    "density_cv": 0.635,
    "target_pearson_r": 0.0,
    "capacity_ratio_input": 0.5,
    "max_weight": 1000,
    "seed": 42,
    "instance_seed": 4201
  },
  "items": [
    {"id": 0, "weight": 180.0, "value": 794.0},
    {"id": 1, "weight": 494.0, "value": 171.0}
  ]
}
```

---

## 4. Kiểm tra chất lượng testcase (`quality.py`)

Sau khi sinh dữ liệu, chạy module phân tích để kiểm tra chất lượng:

```bash
python data/quality.py
```

Script sẽ in bảng thống kê tóm tắt ra terminal và lưu một **dashboard 9 biểu đồ** vào `results/quality/quality_dashboard.png`.
Ngoài ra, module còn lưu:
- `results/quality/metadata_uniformity.png`
- `results/quality/metadata_independence.png`

Tham số CLI:

| Tham số | Mặc định | Mô tả |
|---|---|---|
| `--raw` | `data/raw/` | Thư mục chứa các file JSON đã sinh. |
| `--output` | `results/quality/` | Thư mục lưu ảnh dashboard. |

**Danh sách biểu đồ trong dashboard:**

| # | Biểu đồ | Mục đích |
|---|---|---|
| 1 | Scatter: Weight vs Value | Thấy hình dạng phân phối theo từng mức `target_r` |
| 2 | Scatter: Target vs Actual Pearson r | Kiểm tra độ chính xác của generator |
| 3 | Scatter: Target vs Actual capacity ratio | Kiểm tra tỷ lệ sức chứa |
| 4 | KDE: Weight distribution | Phân phối khối lượng vật phẩm theo `target_r` |
| 5 | KDE: Value distribution | Phân phối giá trị vật phẩm theo `target_r` |
| 6 | KDE: Density (v/w) distribution | Phân phối mật độ giá trị theo `target_r` |
| 7 | Box plot: density_cv theo (n, r) | Độ phân tán mật độ theo kích thước và tương quan |
| 8 | Violin: Pearson r thực tế theo n | Xem r thực tế phân tán ra sao theo n |
| 9 | Heatmap: Correlation metadata | Tương quan giữa các chỉ số metadata |

---

## 5. Ý nghĩa các chỉ số trong `metadata`

**Chỉ số đặc trưng bài toán (tự tính từ dữ liệu):**

| Chỉ số | Ý nghĩa |
|---|---|
| `n` | Số lượng vật phẩm. Quyết định độ phức tạp O(n·W) của DP và O(2ⁿ) của brute-force. |
| `capacity_ratio` | W / sum(w_i). Tiến về 0.5 → bài toán khó nhất; tiến về 0 hoặc 1 → dễ hơn. |
| `pearson_r` | Hệ số tương quan Pearson thực tế giữa `weight` và `value`. Tiến về 1 → phá vỡ khả năng cắt nhánh của Branch & Bound. |
| `density_cv` | CV = std(v/w) / mean(v/w). CV nhỏ → các vật phẩm "tốt ngang nhau" → Greedy dễ sai, Branch & Bound tốn thời gian hơn. |

**Tham số sinh dữ liệu (để truy vết):**

| Chỉ số | Ý nghĩa |
|---|---|
| `target_pearson_r` | Giá trị Pearson r mục tiêu đã cấu hình trong config. |
| `capacity_ratio_input` | Tỷ lệ capacity đầu vào từ config. |
| `max_weight` | Giá trị khối lượng tối đa đầu vào. |
| `seed` | Seed ngẫu nhiên đã dùng để sinh dữ liệu. |
| `instance_seed` | Seed riêng cho từng testcase để tái tạo độc lập. |
