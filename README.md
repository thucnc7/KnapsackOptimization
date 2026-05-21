# Knapsack Benchmark Suite

Dự án hỗ trợ sinh testcase, chạy benchmark, và xuất biểu đồ phân tích cho bài toán Knapsack (0/1, fractional, unbounded).

## Quick start (Windows CMD)

1) Cài dependencies (tối thiểu):

```cmd
pip install -r requirements.txt
```

2) Sinh testcase theo cấu hình `data/test_scenarios.json`:

```cmd
python -u "data\generator.py"
```

Testcase sẽ được ghi vào `data\raw\`.

3) Kiểm tra chất lượng dữ liệu (biểu đồ phân bố/độc lập):

```cmd
python -u "data\quality.py" --raw "data\raw" --output "results\quality"
```

4) Chạy benchmark (timeout 5s):

```cmd
python -u "benchmark\runner.py" --timeout 5 --output "results\csv\benchmark_results_timeout5.csv"
```

5) Chạy notebook phân tích để xuất biểu đồ:

```cmd
python -u -m jupyter nbconvert --to notebook --execute "notebooks\02_analysis_and_plots.ipynb" --output "02_analysis_and_plots.executed.ipynb"
```

Biểu đồ sẽ được ghi vào `results\plots\`.

## Project layout

- `src/`: core models và thuật toán
- `data/`: generator, cấu hình testcase, và dữ liệu raw
- `benchmark/`: runner và metrics
- `results/`: CSV outputs và plots
- `notebooks/`: notebook phân tích
