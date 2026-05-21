"""Build 02_analysis_and_plots.ipynb — Phase 3 & 4.

Phase 3: Scatter plots (time vs n, time vs ratio, time vs pearson_r)
Phase 4: Automated curve fitting with shape detection on time vs n
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def md(src):
    return {"cell_type":"markdown","metadata":{},"source":[src],
            "id":hex(abs(hash(src)))[2:10]}

def code(src):
    return {"cell_type":"code","metadata":{},"source":[src],
            "outputs":[],"execution_count":None,
            "id":hex(abs(hash(src)))[2:10]}

CELLS = []

# ── Title ─────────────────────────────────────────────────────────────────────
CELLS.append(md("""\
# Knapsack Benchmark — Post-Benchmark Analysis

**Phase 3:** Scatter plots of `time_sec` vs each attribute per algorithm.
**Phase 4:** Automated curve fitting (shape detection) on `time_sec` vs `n`.\
"""))

# ── Cell: Setup ───────────────────────────────────────────────────────────────
CELLS.append(code("""\
from __future__ import annotations
import os, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

try:
    from scipy.optimize import curve_fit
    from scipy.stats import pearsonr
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

warnings.filterwarnings("ignore", category=RuntimeWarning)

# ── Design ───────────────────────────────────────────────────────────────────
FIG_BG    = "#0f0f1a"
AX_BG     = "#16213e"
GRID_CLR  = "#2a2a4a"
TEXT_CLR  = "#dde1f0"
MUTED_CLR = "#8890b0"
PAL_LIST  = ["#7b68ee", "#00d4aa", "#ff6b6b", "#ffd166", "#06d6a0",
             "#ef476f", "#118ab2", "#fca311", "#e9c46a"]

plt.rcParams.update({
    "figure.facecolor": FIG_BG, "axes.facecolor": AX_BG,
    "axes.edgecolor": GRID_CLR, "axes.labelcolor": MUTED_CLR,
    "axes.grid": True, "grid.color": GRID_CLR,
    "grid.linewidth": 0.5, "grid.linestyle": "--",
    "text.color": TEXT_CLR,
    "xtick.color": MUTED_CLR, "ytick.color": MUTED_CLR,
    "legend.framealpha": 0.85, "legend.edgecolor": GRID_CLR,
    "legend.facecolor": AX_BG, "legend.labelcolor": TEXT_CLR,
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "figure.dpi": 120, "savefig.dpi": 300,
})

def style_ax(ax, title="", xlabel="", ylabel=""):
    ax.set_title(title, color=TEXT_CLR, pad=8)
    ax.set_xlabel(xlabel, color=MUTED_CLR)
    ax.set_ylabel(ylabel, color=MUTED_CLR)
    ax.set_axisbelow(True)

def algo_pal(algos):
    return {a: PAL_LIST[i % len(PAL_LIST)] for i, a in enumerate(sorted(algos))}

def resolve_root():
    cwd = Path.cwd().resolve()
    for p in [cwd, cwd.parent]:
        if (p / "results").exists():
            return p
    return cwd

ROOT  = resolve_root()
PLOTS = ROOT / "results" / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

def save(fig, name):
    fig.savefig(PLOTS / name, dpi=300, bbox_inches="tight", facecolor=FIG_BG)
    print(f"Saved -> {PLOTS / name}")

print("Root:", ROOT)\
"""))

# ── Cell: Load CSV ────────────────────────────────────────────────────────────
CELLS.append(md("## 1 · Load & Preprocess"))
CELLS.append(code("""\
CSV_PATH = ROOT / "results" / "csv" / "benchmark_results_timeout5.csv"
if not CSV_PATH.exists():
    raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

df = pd.read_csv(CSV_PATH)

for col in ["time_sec","peak_memory_mb","optimal_value",
            "n","capacity","capacity_to_weight_ratio",
            "pearson_corr","density_variance"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

TIMEOUT = int(os.getenv("BENCHMARK_TIMEOUT_SEC", "60"))
df["is_timeout"] = df["status"].str.upper().eq("TIMEOUT")
df["is_error"]   = df["status"].str.upper().eq("ERROR")
df["is_success"] = df["status"].str.upper().eq("SUCCESS")
df["time_plot"]  = df["time_sec"].copy()
df.loc[df["is_timeout"], "time_plot"] = TIMEOUT

ALGOS = sorted(df["algorithm"].unique())
PAL   = algo_pal(ALGOS)

print(f"Rows: {len(df)}  |  Algorithms: {ALGOS}")
print(f"Timeouts: {df['is_timeout'].sum()}  |  Errors: {df['is_error'].sum()}")
display(df[["algorithm","n","time_sec","status"]].head(8))\
"""))

# ── Cell: Phase 3 — Scatter per algorithm ─────────────────────────────────────
CELLS.append(md("""\
## 2 · Scatter Plots: time vs (n, capacity_ratio, pearson_r)

3 separate scatter plots per algorithm.
**Excludes TIMEOUT and ERROR** to avoid skewing.
Y-axis uses log scale when variance is large.\
"""))

CELLS.append(code("""\
df_ok = df[df["is_success"]].copy()

ATTRS = [
    ("n",                          "n (items)"),
    ("capacity_to_weight_ratio",   "capacity_ratio"),
    ("pearson_corr",               "pearson_r (weight-value)"),
]

for algo in ALGOS:
    sub = df_ok[df_ok["algorithm"] == algo]
    if sub.empty:
        print(f"  {algo}: no SUCCESS rows, skip")
        continue

    fig, axes = plt.subplots(1, 3, figsize=(18, 4.5), facecolor=FIG_BG)
    fig.suptitle(f"Algorithm: {algo}",
                 color=TEXT_CLR, fontsize=13, fontweight="bold", y=1.02)

    for ax, (col, xlabel) in zip(axes, ATTRS):
        if col not in sub.columns or sub[col].isna().all():
            ax.text(0.5, 0.5, f"No '{col}' data", ha="center",
                    va="center", color=TEXT_CLR, transform=ax.transAxes)
            style_ax(ax, f"time vs {xlabel}", xlabel, "time_sec")
            continue

        ax.scatter(sub[col], sub["time_sec"],
                   s=22, alpha=0.65, color=PAL[algo],
                   linewidths=0.3, edgecolors=AX_BG, zorder=3)

        # Log scale if variance > 2 orders of magnitude
        tmin, tmax = sub["time_sec"].min(), sub["time_sec"].max()
        if tmax > 0 and tmin > 0 and (tmax / tmin) > 100:
            ax.set_yscale("log")
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda v, _: f"{v:.2g}s")
            )

        style_ax(ax, f"time vs {xlabel}", xlabel, "time_sec")

    fig.tight_layout()
    save(fig, f"scatter_{algo}.png")
    plt.show()\
"""))

# ── Cell: Phase 4 — Curve fitting ─────────────────────────────────────────────
CELLS.append(md("""\
## 3 · Curve Fitting: time vs n (shape detection)

For each algorithm, fit **Linear, Quadratic, Cubic, Exponential** candidates
to the median runtime per n.  Pick the best R² and annotate the plot.\
"""))

CELLS.append(code("""\
if not HAS_SCIPY:
    print("scipy not available; skip curve fitting.")
else:
    # ── Candidate functions ──────────────────────────────────────────────
    def f_linear(x, a, b):
        return a * x + b

    def f_quad(x, a, b, c):
        return a * x**2 + b * x + c

    def f_cubic(x, a, b, c, d):
        return a * x**3 + b * x**2 + c * x + d

    def f_exp(x, a, b):
        return a * np.power(2.0, b * x)

    CANDIDATES = [
        ("Linear  O(N)",   f_linear, (1e-6, 0),              2),
        ("Quadratic O(N^2)", f_quad, (1e-9, 1e-6, 0),        3),
        ("Cubic O(N^3)",   f_cubic,  (1e-12, 1e-9, 1e-6, 0), 4),
        ("Exponential O(2^N)", f_exp, (1e-6, 0.05),           2),
    ]

    def _r_squared(y_true, y_pred):
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    df_fit = df[df["is_success"] & df["time_sec"].gt(0)].copy()

    for algo in ALGOS:
        sub = df_fit[df_fit["algorithm"] == algo]
        if sub.empty or sub["n"].nunique() < 3:
            continue

        medians = sub.groupby("n")["time_sec"].median().reset_index()
        xd = medians["n"].values.astype(float)
        yd = medians["time_sec"].values.astype(float)

        fig, ax = plt.subplots(figsize=(9, 5), facecolor=FIG_BG)

        # Raw data scatter (all points)
        ax.scatter(sub["n"], sub["time_sec"],
                   s=14, alpha=0.30, color=PAL[algo], linewidths=0, label="raw")
        # Median dots
        ax.scatter(xd, yd, s=50, color=PAL[algo], edgecolors="white",
                   linewidths=0.8, zorder=4, label="median")

        best_name, best_r2, best_ys = "None", -1e9, None

        for name, func, p0, n_params in CANDIDATES:
            if len(xd) < n_params:
                continue
            try:
                popt, _ = curve_fit(func, xd, yd, p0=p0, maxfev=20000)
                x_grid = np.linspace(xd.min(), xd.max(), 300)
                y_pred = func(x_grid, *popt)
                y_pred_pts = func(xd, *popt)
                r2 = _r_squared(yd, y_pred_pts)

                if r2 > best_r2:
                    best_r2 = r2
                    best_name = name
                    best_ys = (x_grid, y_pred)
            except Exception:
                pass

        # Draw best fit
        if best_ys is not None:
            ax.plot(best_ys[0], best_ys[1], "--", color=MUTED_CLR, lw=2,
                    label=f"Best: {best_name}", zorder=5)

        # Annotate
        box_text = f"Best fit: {best_name}\\nR² = {best_r2:.4f}"
        ax.text(0.02, 0.96, box_text,
                transform=ax.transAxes, fontsize=10, va="top",
                color=TEXT_CLR, fontweight="bold",
                bbox=dict(facecolor=AX_BG, edgecolor=GRID_CLR,
                          alpha=0.9, boxstyle="round,pad=0.4"))

        tmin, tmax = yd.min(), yd.max()
        if tmax > 0 and tmin > 0 and (tmax / tmin) > 50:
            ax.set_yscale("log")

        ax.legend(fontsize=8, loc="lower right")
        style_ax(ax, f"Curve Fit: {algo}", "n (items)", "time_sec (median)")
        fig.tight_layout()
        save(fig, f"curvefit_{algo}.png")
        plt.show()\
"""))

# ── Write notebook ────────────────────────────────────────────────────────────
nb = {
    "nbformat": 4, "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name":"Python 3","language":"python","name":"python3"},
        "language_info": {"name":"python","version":"3.11"},
    },
    "cells": CELLS,
}

out = HERE / "02_analysis_and_plots.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Written: {out}  ({len(CELLS)} cells)")
