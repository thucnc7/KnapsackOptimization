# Knapsack Benchmark Suite

Du an ho tro sinh testcase, chay benchmark, va xuat bieu do phan tich cho bai toan Knapsack (0/1, fractional, unbounded).

## Quick start (Windows CMD)

1) Cai dependencies:

```cmd
pip install -r requirements.txt
```

2) Sinh testcase theo cau hinh `data/test_scenarios.json`:

```cmd
python -u "data\generator.py"
```

Testcase se duoc ghi vao `data\raw\`.
Generator su dung **Gaussian jitter** (n va capacity_ratio dao dong quanh gia tri neo)
va **rejection sampling** cho Pearson r >= 0.9 de dam bao chat luong du lieu.

3) Kiem tra chat luong du lieu (bieu do Gaussian bell + scatter):

```cmd
python -u "data\quality.py" --raw "data\raw" --output "results\quality"
```

Dashboard se xac nhan n_actual, ratio_actual, pearson_actual tao thanh phan phoi chuong Gauss quanh gia tri neo.

4) Chay benchmark (timeout 5s):

```cmd
python -u "benchmark\runner.py" --timeout 5 --output "results\csv\benchmark_results_timeout5.csv"
```

5) Tao notebook phan tich (Phase 3 + 4):

```cmd
python -u "notebooks\build_notebook.py"
python -u -m jupyter nbconvert --to notebook --execute "notebooks\02_analysis_and_plots.ipynb" --output "02_analysis_and_plots.executed.ipynb"
```

Bieu do se duoc ghi vao `results\plots\`:
- `scatter_{Algorithm}.png` — 3 scatter plots (time vs n, ratio, pearson_r) cho tung thuat toan
- `curvefit_{Algorithm}.png` — Curve fitting tu dong (Linear/Quadratic/Cubic/Exponential) voi R²

## Project layout

- `src/` — Core models va cac thuat toan giai (DP, Branch&Bound, Greedy, Simplex...)
- `data/` — Generator (Gaussian jitter + rejection), cau hinh testcase, quality plots
- `benchmark/` — Runner va metrics
- `results/` — CSV outputs, quality dashboard, va analysis plots
- `notebooks/` — Notebook phan tich hau benchmark (scatter + curve fit)
