# Benchmark Runner

Thư mục này chứa bộ máy benchmark chạy cách ly theo tiến trình. Mỗi thuật toán được chạy trong một process riêng để khi **timeout** hoặc **OOM** xảy ra, toàn bộ suite vẫn an toàn.

## Chạy nhanh

Từ thư mục gốc của dự án:

```cmd
python -u "E:\Antigravity Workspace\Knapsack\KnapsackOptimization\benchmark\runner.py" --limit 1 --timeout 5
```

Ví dụ tạo file riêng cho timeout 5s:

```cmd
python -u "E:\Antigravity Workspace\Knapsack\KnapsackOptimization\benchmark\runner.py" --timeout 5 --output "E:\Antigravity Workspace\Knapsack\KnapsackOptimization\results\csv\benchmark_results_timeout5.csv"
```

## Tùy chọn lệnh

- `--raw`: thư mục chứa các instance JSON (mặc định `data/raw`)
- `--output`: file CSV đầu ra (mặc định `results/csv/benchmark_results.csv`)
- `--timeout`: thời gian tối đa cho mỗi lần chạy (giây, mặc định 60)
- `--limit`: giới hạn số instance (0 = chạy hết)

## Cột trong CSV

CSV xuất ra gồm các cột:

- `test_id`, `algorithm`, `knapsack_type`, `status`
- `time_sec`, `peak_memory_mb`, `optimal_value`
- `n`, `capacity`, `capacity_to_weight_ratio`, `pearson_corr`, `density_variance`

## Trạng thái `status`

- `SUCCESS`: thuật toán chạy xong, có nghiệm.
- `TIMEOUT`: vượt quá `--timeout`.
- `OOM`: hết bộ nhớ trong tiến trình thuật toán.
- `ERROR`: lỗi khác (exception).

## Ghi chú

- Danh sách thuật toán được khai báo trong `benchmark/runner.py`.
- `tqdm` dùng để hiển thị progress bar và đã nằm trong `requirements.txt`.
