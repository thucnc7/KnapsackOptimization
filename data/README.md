# Data Management Component

Thư mục này quản lý cấu hình và tự động sinh tập dữ liệu thử nghiệm (Benchmark Datasets)
cho bài toán Ba lô 0/1. Hệ thống chạy theo cơ chế **config-driven**, tách biệt hoàn toàn
giữa tham số kịch bản và mã nguồn sinh dữ liệu.

## 1. Cấu hình kịch bản (`test_scenarios.json`)

File `data/test_scenarios.json` lưu một mảng các kịch bản. Bạn có thể thay đổi các tham
số để điều khiển số lượng và tính chất dữ liệu đầu ra.

Ví dụ cấu hình:

```json
[
  {
    "name": "scaling_n_test",
    "n_values": [10, 50, 100, 500],
    "max_weight": 1000,
    "capacity_ratios": [0.1, 0.5, 0.9],
    "strategies": ["uncorrelated", "weakly_correlated", "strongly_correlated"],
    "instances_per_config": 5
  }
]
```

Ý nghĩa tham số:

- `name`: Tên kịch bản (dùng làm tiền tố đặt tên file).
- `n_values`: Danh sách số lượng vật phẩm cần sinh.
- `max_weight`: Giá trị khối lượng tối đa của mỗi vật phẩm (mặc định `1000`).
- `capacity_ratios`: Tỷ lệ sức chứa so với tổng khối lượng (`sum(w_i)`).
- `strategies`: Chiến lược phân phối dữ liệu đầu vào.
- `instances_per_config`: Số lượng file sinh ra cho mỗi tổ hợp tham số.

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

| Tham số    | Mặc định                    | Mô tả                                      |
|------------|-----------------------------|--------------------------------------------|
| `--config` | `data/test_scenarios.json`  | Đường dẫn file cấu hình kịch bản          |
| `--seed`   | `42`                        | Seed ngẫu nhiên, đảm bảo kết quả tái tạo  |

> **Lưu ý:** Cùng `--seed` sẽ luôn sinh ra **đúng bộ dữ liệu giống nhau**,
> đảm bảo tính reproducible cho thực nghiệm.

Script sẽ đọc cấu hình, tạo tổ hợp tham số, sinh dữ liệu bằng `numpy`, tính các chỉ số
thống kê định lượng, và xuất JSON vào `data/raw/`.

## 3. Định dạng dữ liệu đầu ra (`data/raw/`)

Mỗi file đại diện cho một bài toán cụ thể, đặt tên theo quy ước:

```
{scenario_name}_n{n}_wmax{max_weight}_r{ratio}_{strategy}_{index}.json
```

Ví dụ nội dung JSON:

```json
{
  "test_id": "algorithmic_scaling_test_n10_wmax1000_r0.5_uncorrelated_01",
  "metadata": {
    "n": 10,
    "capacity": 1772,
    "capacity_to_total_weight_ratio": 0.4999,
    "weight_mean": 354.5,
    "weight_std_dev": 216.68,
    "value_mean": 576.2,
    "value_std_dev": 255.36,
    "pearson_correlation_coefficient": 0.1465,
    "density_variance": 1.9455,
    "strategy": "uncorrelated",
    "capacity_ratio_input": 0.5,
    "max_weight": 1000,
    "seed": 42
  },
  "items": [
    {"id": 0, "w": 450, "v": 460},
    {"id": 1, "w": 120, "v": 130}
  ]
}
```

## 4. Ý nghĩa các chỉ số trong `metadata`

**Chỉ số thống kê:**

- `capacity_to_total_weight_ratio`: Tỷ lệ sức chứa / tổng khối lượng, đo độ thắt chặt ràng buộc.
- `weight_mean`, `weight_std_dev`: Trung bình và độ lệch chuẩn khối lượng.
- `value_mean`, `value_std_dev`: Trung bình và độ lệch chuẩn giá trị.
- `pearson_correlation_coefficient`: Hệ số tương quan Pearson giữa trọng lượng và giá trị.
- `density_variance`: Phương sai mật độ giá trị với `d_i = v_i / w_i`.

**Tham số sinh dữ liệu (truy vết):**

- `strategy`: Chiến lược phân phối đã dùng (`uncorrelated`, `weakly_correlated`, `strongly_correlated`).
- `capacity_ratio_input`: Tỷ lệ capacity đầu vào từ config.
- `max_weight`: Giá trị khối lượng tối đa đầu vào.
- `seed`: Seed ngẫu nhiên đã dùng để sinh dữ liệu.
