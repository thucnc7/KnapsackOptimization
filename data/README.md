# Data Management Component

Thu muc nay quan ly cau hinh va tu dong sinh tap du lieu thu nghiem (Benchmark Datasets)
cho bai toan Ba lo 0/1. He thong chay theo co che **config-driven**, tach biet hoan toan
giua tham so kich ban va ma nguon sinh du lieu.

---

## 1. Cau hinh kich ban (`test_scenarios.json`)

File `data/test_scenarios.json` luu mot mang cac kich ban:

```json
[
  {
    "name": "benchmark_core",
    "description": "Mo ta kich ban",
    "n_values": [10, 50, 100, 500],
    "max_weight": 1000,
    "capacity_ratios": [0.1, 0.5, 0.9],
    "pearson_r_targets": [0.0, 0.5, 0.95],
    "instances_per_config": 5
  }
]
```

| Tham so | Bat buoc | Mo ta |
|---|---|---|
| `name` | Co | Ten kich ban (tien to ten file). |
| `description` | Khong | Mo ta muc dich kich ban. |
| `n_values` | Co | Danh sach so luong vat pham (gia tri neo). |
| `max_weight` | Khong | Khoi luong toi da moi vat pham (mac dinh `1000`). |
| `capacity_ratios` | Co | Ty le suc chua W so voi tong khoi luong (gia tri neo). |
| `pearson_r_targets` | Co | He so tuong quan Pearson muc tieu giua `weight` va `value`. |
| `instances_per_config` | Co | So file sinh ra cho moi to hop tham so. |

> **Ghi chu ve `pearson_r_targets`:**
> - `0.0` — Hoan toan ngau nhien (uncorrelated).
> - `0.5` — Tuong quan vua phai (weakly correlated).
> - `0.95` — Tuong quan cao (strongly correlated) — lam suy yeu kha nang cat nhanh cua Branch & Bound.

---

## 2. Thuc thi sinh du lieu (`generator.py`)

```bash
# Chay voi seed mac dinh (42)
python data/generator.py

# Chay voi seed tuy chon
python data/generator.py --seed 123

# Chay voi file config khac
python data/generator.py --config path/to/config.json --seed 42
```

| Tham so | Mac dinh | Mo ta |
|---|---|---|
| `--config` | `data/test_scenarios.json` | Duong dan file cau hinh. |
| `--seed` | `42` | Seed ngau nhien (reproducible). |

### Thuat toan sinh du lieu (v3)

**Gaussian Jitter:** Moi gia tri trong config la **gia tri neo (anchor)**, gia tri thuc te duoc lam nhieu quanh no:

- `n_actual = N(n_anchor, 0.10 * n_anchor)` — clamp >= 2
- `ratio_actual = N(ratio_anchor, 0.05 * ratio_anchor)` — clamp [0.01, 1.0]

Dieu nay tao ra phan phoi Gauss tu nhien quanh moi gia tri cau hinh, giup du lieu test da dang hon.

**Cholesky Method:** Kiem soat tuong quan Pearson:
- Sinh `x`, `z ~ N(0,1)` doc lap.
- Tao `y = r*x + sqrt(1-r²)*z`.
- Scale ca hai ve `[1, max_weight]`.

**Rejection Sampling:** Khi `target_pearson_r >= 0.9`:
- Kiem tra tuong quan thuc te bang `scipy.stats.pearsonr`.
- Neu sai lech > 0.03, loai bo va sinh lai (toi da 200 lan thu).

---

## 3. Dinh dang du lieu dau ra (`data/raw/`)

Ten file theo quy uoc:

```
{scenario}_n{n_anchor}_wmax{max_weight}_cr{ratio_anchor}_pr{target_r}_{index}.json
```

Vi du: `benchmark_core_n100_wmax1000_cr0.5_pr0.95_03.json`

Noi dung JSON:

```json
{
  "test_id": "benchmark_core_n100_wmax1000_cr0.5_pr0.95_01",
  "capacity": 23514.7,
  "metadata": {
    "n": 110,
    "capacity_ratio": 0.5299,
    "pearson_r": 0.9643,
    "density_cv": 0.0964,
    "n_anchor": 100,
    "n_actual": 110,
    "target_pearson_r": 0.95,
    "capacity_ratio_anchor": 0.5,
    "capacity_ratio_actual": 0.5299,
    "max_weight": 1000,
    "seed": 42,
    "instance_seed": 42009377
  },
  "items": [
    {"id": 0, "weight": 180.0, "value": 794.0}
  ]
}
```

---

## 4. Kiem tra chat luong testcase (`quality.py`)

```bash
python data/quality.py
```

Luu dashboard vao `results/quality/quality_dashboard.png`.

| Tham so | Mac dinh | Mo ta |
|---|---|---|
| `--raw` | `data/raw/` | Thu muc chua cac file JSON da sinh. |
| `--output` | `results/quality/` | Thu muc luu anh dashboard. |

**Dashboard 6 bieu do (Phase 2 — Gaussian Verification):**

| # | Bieu do | Muc dich |
|---|---|---|
| 1 | Histogram + Normal fit: n_actual | Chung minh n_actual tao phan phoi Gauss quanh n_anchor |
| 2 | Histogram + Normal fit: ratio_actual | Chung minh ratio_actual tao Gauss quanh ratio_anchor |
| 3 | Histogram + Normal fit: pearson_r | Chung minh pearson_r thuc te phan phoi quanh target |
| 4 | Scatter: n_anchor vs n_actual | Nhin do trai (jitter spread) cua n |
| 5 | Scatter: ratio_anchor vs ratio_actual | Nhin do trai cua capacity ratio |
| 6 | Scatter: target_r vs actual_r (theo n) | Do chinh xac Pearson r, mau theo n |

Truc X cua cac histogram la **gia tri thuc te lien tuc**, truc Y la **mat do (density)**, kem duong Normal fit.

---

## 5. Y nghia cac chi so trong `metadata`

**Chi so dac trung bai toan (tu tinh tu du lieu):**

| Chi so | Y nghia |
|---|---|
| `n` | So luong vat pham thuc te (= `n_actual`, sau Gaussian jitter). |
| `capacity_ratio` | W / sum(w_i) thuc te (sau jitter). |
| `pearson_r` | He so tuong quan Pearson thuc te giua `weight` va `value`. |
| `density_cv` | CV = std(v/w) / mean(v/w). CV nho → Greedy de sai, B&B ton thoi gian. |

**Tham so neo va truy vet:**

| Chi so | Y nghia |
|---|---|
| `n_anchor` | Gia tri n goc tu config (truoc jitter). |
| `n_actual` | Gia tri n thuc te (sau Gaussian jitter). |
| `target_pearson_r` | Pearson r muc tieu tu config. |
| `capacity_ratio_anchor` | Ratio goc tu config. |
| `capacity_ratio_actual` | Ratio thuc te (sau jitter). |
| `max_weight` | Khoi luong toi da dau vao. |
| `seed` | Global seed. |
| `instance_seed` | Seed rieng cho tung testcase (tai tao doc lap). |
