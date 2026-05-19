# Knapsack Benchmark Suite

This project scaffolds a benchmarking suite for comparing 0/1 knapsack algorithms.

## Quick start

1. Create data instances:

```
python data/generator.py -n 50 100 --instances 3 --ratio 0.5
```

2. Generated JSON files appear in `data/raw/`.

## Project layout

- `src/`: core models and algorithm implementations
- `data/`: data generator and raw data output
- `benchmark/`: metrics and runner scaffolding
- `results/`: logs, CSV outputs, and plots
- `notebooks/`: analysis notebooks
