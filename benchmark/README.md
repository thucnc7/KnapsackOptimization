# Benchmark Runner

This folder contains the process-isolated benchmarking engine. Each algorithm is executed in its own process so that timeouts or OOM events do not crash the suite.

## Quick Start

From the project root:

```cmd
python -u "E:\Antigravity Workspace\Knapsack\KnapsackOptimization\benchmark\runner.py" --limit 1 --timeout 5
```

## Command Options

- `--raw`: directory containing JSON instances (default: `data/raw`)
- `--output`: CSV output file (default: `results/csv/benchmark_results.csv`)
- `--timeout`: per-run timeout in seconds (default: 60)
- `--limit`: limit number of instances (0 = all)

## Output Columns

The CSV file includes the following columns:

- `test_id`, `algorithm`, `knapsack_type`, `status`
- `time_sec`, `peak_memory_mb`, `optimal_value`
- `n`, `capacity`, `capacity_to_weight_ratio`, `pearson_corr`, `density_variance`

## Notes

- The algorithm registry is defined in `benchmark/runner.py` using placeholder classes.
- `tqdm` is required for the progress bar and is already listed in `requirements.txt`.
