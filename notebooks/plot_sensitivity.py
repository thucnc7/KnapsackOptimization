"""Plotting script for Sensitivity Analysis benchmark results.

Generates dark-themed plots and copies them to the LaTeX directory.
"""

from __future__ import annotations

import shutil
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT_DIR / "results" / "csv" / "sensitivity_results.csv"
OUTPUT_DIR = ROOT_DIR / "results" / "plots" / "sensitivity"
LATEX_DIR = ROOT_DIR.parent / "latex" / "image" / "sensitivity"

# Design tokens
FIG_BG    = "#0f0f1a"
AX_BG     = "#16213e"
GRID_CLR  = "#2a2a4a"
TEXT_CLR  = "#dde1f0"
MUTED_CLR = "#8890b0"
COLORS    = ["#ff6b6b", "#00d4aa"]  # Scratch = Coral, Warm-start = Teal
DIAG_CLR  = "#ffd166"

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

def generate_plots():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LATEX_DIR.mkdir(parents=True, exist_ok=True)
    
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Benchmark results CSV not found at: {CSV_PATH}")
        
    df = pd.read_csv(CSV_PATH)
    
    # ── 1. Runtime Comparison (Grouped Bar Chart) ───────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5), facecolor=FIG_BG)
    
    # Calculate means in milliseconds
    df_ms = df.copy()
    df_ms["time_scratch_ms"] = df_ms["time_scratch_sec"] * 1000.0
    df_ms["time_warm_ms"] = df_ms["time_warm_sec"] * 1000.0
    
    means = df_ms.groupby("scenario")[["time_scratch_ms", "time_warm_ms"]].mean().reset_index()
    
    # Melt for seaborn
    melted_time = pd.melt(
        means, id_vars=["scenario"], 
        value_vars=["time_scratch_ms", "time_warm_ms"],
        var_name="Method", value_name="time_ms"
    )
    melted_time["Method"] = melted_time["Method"].map({
        "time_scratch_ms": "Re-solve from Scratch",
        "time_warm_ms": "Dual Simplex Warm-start"
    })
    
    sns.barplot(
        data=melted_time, x="scenario", y="time_ms", hue="Method",
        palette=COLORS, ax=ax, edgecolor=GRID_CLR, linewidth=0.5
    )
    
    # Use log scale since values span from 0.02ms to 8ms
    ax.set_yscale("log")
    style_ax(
        ax, 
        title="Average Runtime: Re-solve vs. Warm-start (Log Scale)",
        xlabel="Scenario", 
        ylabel="Execution Time (milliseconds)"
    )
    # Customize tick formatter for log scale
    import matplotlib.ticker as mticker
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.3f"))
    
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "runtime_comparison.png")
    shutil.copy(OUTPUT_DIR / "runtime_comparison.png", LATEX_DIR / "runtime_comparison.png")
    plt.close(fig)
    
    # ── 2. Speedup Distribution (Boxenplot / Boxplot) ───────────────────────
    fig, ax = plt.subplots(figsize=(6, 5), facecolor=FIG_BG)
    
    sns.boxplot(
        data=df, x="scenario", y="speedup", 
        ax=ax, palette=COLORS * 2, hue="scenario", legend=False,
        boxprops=dict(edgecolor=TEXT_CLR, facecolor=AX_BG, alpha=0.6),
        whiskerprops=dict(color=MUTED_CLR),
        capprops=dict(color=MUTED_CLR),
        medianprops=dict(color=DIAG_CLR, linewidth=2.0)
    )
    
    ax.set_yscale("log")
    style_ax(
        ax, 
        title="Speedup Factor Distribution (Log Scale)",
        xlabel="Scenario", 
        ylabel="Speedup (Scratch Time / Warm Time)"
    )
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%g"))
    
    # Add mean text annotations
    for i, scen in enumerate(["capacity", "value", "volume"]):
        mean_val = df[df["scenario"] == scen]["speedup"].mean()
        ax.text(
            i, mean_val * 1.2, f"Mean: {mean_val:.1f}x", 
            ha="center", va="bottom", color=DIAG_CLR, fontweight="bold", fontsize=9
        )
        
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "speedup_distribution.png")
    shutil.copy(OUTPUT_DIR / "speedup_distribution.png", LATEX_DIR / "speedup_distribution.png")
    plt.close(fig)
    
    # ── 3. Pivot Iteration Comparison ───────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5), facecolor=FIG_BG)
    
    iter_means = df.groupby("scenario")[["iter_scratch", "iter_warm"]].mean().reset_index()
    melted_iter = pd.melt(
        iter_means, id_vars=["scenario"], 
        value_vars=["iter_scratch", "iter_warm"],
        var_name="Method", value_name="iterations"
    )
    melted_iter["Method"] = melted_iter["Method"].map({
        "iter_scratch": "Re-solve from Scratch",
        "iter_warm": "Dual Simplex Warm-start"
    })
    
    sns.barplot(
        data=melted_iter, x="scenario", y="iterations", hue="Method",
        palette=COLORS, ax=ax, edgecolor=GRID_CLR, linewidth=0.5
    )
    
    style_ax(
        ax, 
        title="Average Pivot Iterations: Re-solve vs. Warm-start",
        xlabel="Scenario", 
        ylabel="Number of Pivot Steps"
    )
    
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "iterations_comparison.png")
    shutil.copy(OUTPUT_DIR / "iterations_comparison.png", LATEX_DIR / "iterations_comparison.png")
    plt.close(fig)
    
    print("Plots generated and copied to LaTeX directory successfully!")

if __name__ == "__main__":
    generate_plots()
