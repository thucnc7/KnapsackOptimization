# Knapsack Optimization Visualizer

Một webapp Flask cung cấp dashboard và nhiều chế độ chạy để khám phá kết quả benchmark
của các thuật toán knapsack đã được implement trong repo này (`main`, `Hoàng_Đạt`,
`feature/data-generator` đã được merge).

## Các chế độ chạy (modes)

| Mode | Mô tả |
|------|------|
| **Dashboard** | Tổng quan từ CSV benchmark: success/timeout/error, time/memory trung bình, thời gian theo N, bảng chi tiết theo thuật toán. |
| **So sánh** | Paired comparison giữa 2 thuật toán: scatter time log-log, value khớp/lệch, speedup theo N. |
| **Single Solver** | Chạy 1 thuật toán trên 1 instance JSON có sẵn trong `data/raw/`. Hiển thị items được chọn, weight/value scatter, metrics. |
| **Multi-Solver** | Chạy nhiều thuật toán cùng lúc trên 1 instance. So sánh time, memory, optimal value. |
| **Custom Instance** | Builder tay: nhập capacity và list items, chạy bất kỳ thuật toán nào. |
| **Data Quality** | Hiển thị cấu hình `test_scenarios.json` + các biểu đồ chất lượng đã được sinh ra (`results/quality/`, `results/plots/`). |
| **Job Runner** | Chạy nền các script Python: `benchmark/runner.py`, `data/generator.py`, `data/quality.py` với log streaming realtime. |

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy server

```bash
python -m webapp.app --port 5000 --debug
```

Mở trình duyệt: <http://127.0.0.1:5000>

## Kiến trúc

```
webapp/
├── app.py                # Flask entry point
├── api/
│   ├── benchmark_api.py  # /api/benchmark/* - CSV summary
│   ├── data_api.py       # /api/data/* - instances, scenarios, algorithms
│   ├── solver_api.py     # /api/solver/* - chạy trực tiếp 1 hoặc nhiều thuật toán
│   └── runner_api.py     # /api/runner/* - quản lý subprocess jobs
├── static/
│   ├── css/main.css
│   └── js/
│       ├── utils.js
│       ├── main.js       # mode switcher
│       ├── dashboard.js
│       ├── comparison.js
│       ├── solver.js
│       ├── multi.js
│       ├── custom.js
│       ├── quality.js
│       └── runner.js
└── templates/index.html  # SPA-style với tabs
```

### Backend
- **Flask** với 4 blueprint mounted dưới `/api/*`.
- Solver API gọi trực tiếp các class trong `src/algorithms/` thông qua
  registry `benchmark.runner.get_algorithm_registry()`, có đo `tracemalloc`
  cho memory.
- Runner API spawn subprocess (`benchmark.runner`, `data.generator`, `data.quality`)
  và stream log tới browser qua polling 2s.

### Frontend
- Vanilla JS modules + Chart.js 4 từ CDN. Không cần build step.
- Mỗi panel lazy-init khi user chuyển tab.

## API endpoints

| Method | Endpoint | Mô tả |
|--------|----------|------|
| GET | `/api/benchmark/files` | List file CSV trong `results/csv/` |
| GET | `/api/benchmark/raw?file=&algorithm=&status=&limit=` | Raw rows filter |
| GET | `/api/benchmark/summary?file=` | Aggregates by algorithm + by N |
| GET | `/api/benchmark/compare?file=&a=&b=` | Paired comparison 2 algorithms |
| GET | `/api/data/instances?q=&limit=&offset=` | List instance files |
| GET | `/api/data/instance/<id>` | Lấy payload JSON instance |
| GET | `/api/data/scenarios` | Trả về `test_scenarios.json` |
| GET | `/api/data/algorithms` | List thuật toán có sẵn |
| GET | `/api/data/quality-images` | List ảnh trong `results/quality/` + `results/plots/` |
| POST | `/api/solver/run` | `{algorithm, instance_id?, instance?}` → chạy live |
| POST | `/api/solver/run-multi` | `{algorithms, instance_id?, instance?}` |
| POST | `/api/runner/benchmark` | `{timeout, limit, output}` start job |
| POST | `/api/runner/generator` | `{seed}` start job |
| POST | `/api/runner/quality` | start quality.py |
| GET | `/api/runner/jobs` | List jobs |
| GET | `/api/runner/jobs/<id>/log?tail=1` | Đọc log job |
| DELETE | `/api/runner/jobs/<id>` | Terminate job |

## Lưu ý

- Một số thuật toán (DP, Backtracking, Simplex) có thể chạy rất lâu trên
  instance lớn (n ≥ 1000). Khi chạy ở mode Solver/Multi, KHÔNG có timeout —
  hãy chọn instance vừa với khả năng của thuật toán hoặc dùng Greedy/BranchAndBound.
- Custom instance không hỗ trợ unbounded knapsack tốt — các DP/BnB hiện đang
  tối ưu cho 0/1.
