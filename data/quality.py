"""Analyze and visualize the quality of generated knapsack benchmark instances."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ── Palette ──────────────────────────────────────────────────────────────────
PALETTE = "viridis"
STYLE   = "dark_background"
FIG_BG  = "#0f0f1a"
AX_BG   = "#1a1a2e"
TEXT_COLOR = "#e0e0e0"
ACCENT  = "#7b68ee"


class TestcaseQualityAnalyzer:
    """Load generated benchmark instances and produce a quality report.

    Usage
    -----
    >>> analyzer = TestcaseQualityAnalyzer("data/raw")
    >>> analyzer.plot_all(output_dir="results/quality")
    >>> analyzer.print_summary()
    """

    # ── Construction ─────────────────────────────────────────────────────────

    def __init__(self, raw_dir: str | Path) -> None:
        self.raw_dir = Path(raw_dir)
        self._records: List[Dict[str, Any]] = self._load_all()
        self.df: pd.DataFrame = self._build_dataframe()

    def _load_all(self) -> List[Dict[str, Any]]:
        """Load every JSON file from raw_dir into a flat list of records."""
        files = sorted(self.raw_dir.glob("*.json"))
        if not files:
            raise FileNotFoundError(f"No JSON files found in {self.raw_dir}")

        records = []
        for path in files:
            raw = json.loads(path.read_text(encoding="utf-8"))
            meta = raw.get("metadata", {})
            record = {
                "test_id":          raw["test_id"],
                "capacity":         raw["capacity"],
                "n":                int(meta.get("n", 0)),
                "capacity_ratio":   float(meta.get("capacity_ratio", 0)),
                "pearson_r":        float(meta.get("pearson_r", 0)),
                "density_cv":       float(meta.get("density_cv", 0)),
                "target_pearson_r": float(meta.get("target_pearson_r", float("nan"))),
                "capacity_ratio_input": float(meta.get("capacity_ratio_input", float("nan"))),
                "max_weight":       int(meta.get("max_weight", 0)),
                "seed":             int(meta.get("seed", 0)),
            }
            # Derive per-item arrays for distribution plots
            items = raw.get("items", [])
            record["weights"] = [it["weight"] for it in items]
            record["values"]  = [it["value"]  for it in items]
            record["densities"] = [
                it["value"] / it["weight"] if it["weight"] != 0 else 0.0
                for it in items
            ]
            records.append(record)
        return records

    def _build_dataframe(self) -> pd.DataFrame:
        """Build a summary DataFrame (one row per instance, no item arrays)."""
        rows = [
            {k: v for k, v in rec.items()
             if k not in ("weights", "values", "densities")}
            for rec in self._records
        ]
        df = pd.DataFrame(rows)
        df["n_label"] = "n=" + df["n"].astype(str)
        df["target_r_label"] = "r≈" + df["target_pearson_r"].map(
            lambda x: str(x) if not np.isnan(x) else "?"
        )
        return df

    # ── Public API ────────────────────────────────────────────────────────────

    def print_summary(self) -> None:
        """Print a concise statistical summary to stdout."""
        print("=" * 60)
        print("  TESTCASE QUALITY SUMMARY")
        print("=" * 60)
        print(f"  Total instances : {len(self.df)}")
        print(f"  n values        : {sorted(self.df['n'].unique())}")
        print(f"  Target r values : {sorted(self.df['target_pearson_r'].dropna().unique())}")
        print(f"  Capacity ratios : {sorted(self.df['capacity_ratio_input'].dropna().unique())}")
        print()
        key_cols = ["n", "pearson_r", "density_cv", "capacity_ratio"]
        print(self.df[key_cols].describe().round(4).to_string())
        print()

        # Correlation accuracy
        valid = self.df.dropna(subset=["target_pearson_r"])
        if not valid.empty:
            valid = valid.copy()
            valid["r_error"] = (valid["pearson_r"] - valid["target_pearson_r"]).abs()
            print("  Pearson-r accuracy (target vs actual):")
            print(valid.groupby("target_pearson_r")["r_error"].describe().round(4).to_string())
        print("=" * 60)

    def plot_all(self, output_dir: str | Path | None = None) -> None:
        """Generate the full quality dashboard (7 subplots) and save/show it."""
        plt.style.use(STYLE)
        fig = plt.figure(figsize=(22, 20), facecolor=FIG_BG)
        fig.suptitle(
            "Knapsack Benchmark — Testcase Quality Dashboard",
            fontsize=18, color=TEXT_COLOR, fontweight="bold", y=0.98,
        )
        gs = gridspec.GridSpec(
            3, 3, figure=fig,
            hspace=0.42, wspace=0.35,
            left=0.06, right=0.97, top=0.93, bottom=0.06,
        )

        ax1 = fig.add_subplot(gs[0, 0])   # Weight vs Value scatter
        ax2 = fig.add_subplot(gs[0, 1])   # Target vs Actual Pearson r
        ax3 = fig.add_subplot(gs[0, 2])   # Capacity ratio: target vs actual
        ax4 = fig.add_subplot(gs[1, 0])   # Weight distribution
        ax5 = fig.add_subplot(gs[1, 1])   # Value distribution
        ax6 = fig.add_subplot(gs[1, 2])   # Density (v/w) distribution
        ax7 = fig.add_subplot(gs[2, 0])   # density_cv by n
        ax8 = fig.add_subplot(gs[2, 1])   # Pearson r by n
        ax9 = fig.add_subplot(gs[2, 2])   # Metadata correlation heatmap

        self._plot_weight_value_scatter(ax1)
        self._plot_target_vs_actual_r(ax2)
        self._plot_capacity_ratio_accuracy(ax3)
        self._plot_distribution(ax4, field="weights", label="Weight")
        self._plot_distribution(ax5, field="values",  label="Value")
        self._plot_distribution(ax6, field="densities", label="Density (v/w)")
        self._plot_density_cv_by_n(ax7)
        self._plot_pearson_r_by_n(ax8)
        self._plot_metadata_heatmap(ax9)

        if output_dir:
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            save_path = out / "quality_dashboard.png"
            fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=FIG_BG)
            print(f"Dashboard saved -> {save_path}")

        plt.show()

    # ── Individual plots ──────────────────────────────────────────────────────

    def _style_ax(self, ax: plt.Axes, title: str) -> None:
        ax.set_facecolor(AX_BG)
        ax.set_title(title, color=TEXT_COLOR, fontsize=11, pad=8)
        ax.tick_params(colors=TEXT_COLOR, labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#444466")
        ax.xaxis.label.set_color(TEXT_COLOR)
        ax.yaxis.label.set_color(TEXT_COLOR)

    def _plot_weight_value_scatter(self, ax: plt.Axes) -> None:
        """Scatter weight vs value for a sample of instances, coloured by target_pearson_r."""
        # Sample at most 3 instances per target_r group to avoid overplotting
        sample = (
            self.df.groupby("target_pearson_r", group_keys=False)
            .apply(lambda g: g.sample(min(3, len(g)), random_state=0), include_groups=False)
        )
        for rec in self._records:
            if rec["test_id"] not in set(sample["test_id"]):
                continue
            tr = rec.get("target_pearson_r") or 0.0
            color = plt.cm.plasma(0.1 + 0.8 * ((tr + 1) / 2))
            ax.scatter(
                rec["weights"], rec["values"],
                alpha=0.4, s=10, color=color, linewidths=0,
            )

        # Legend
        for r_val in sorted(self.df["target_pearson_r"].dropna().unique()):
            color = plt.cm.plasma(0.1 + 0.8 * ((r_val + 1) / 2))
            ax.scatter([], [], color=color, label=f"r≈{r_val}", s=30)
        ax.legend(
            fontsize=7, facecolor=AX_BG, edgecolor="#444466",
            labelcolor=TEXT_COLOR, loc="upper left",
        )
        ax.set_xlabel("Weight"); ax.set_ylabel("Value")
        self._style_ax(ax, "Weight vs Value (sample, coloured by target r)")

    def _plot_target_vs_actual_r(self, ax: plt.Axes) -> None:
        """Scatter: target Pearson r vs realised Pearson r per instance."""
        valid = self.df.dropna(subset=["target_pearson_r"])
        if valid.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", color=TEXT_COLOR)
            self._style_ax(ax, "Target vs Actual Pearson r")
            return

        # Group by n for colour
        n_vals = sorted(valid["n"].unique())
        palette = plt.colormaps["cool"].resampled(len(n_vals))
        for i, n_val in enumerate(n_vals):
            sub = valid[valid["n"] == n_val]
            ax.scatter(
                sub["target_pearson_r"], sub["pearson_r"],
                label=f"n={n_val}", s=20, alpha=0.7,
                color=palette(i), linewidths=0,
            )

        # Perfect accuracy diagonal
        lo = min(valid["target_pearson_r"].min(), valid["pearson_r"].min()) - 0.05
        hi = max(valid["target_pearson_r"].max(), valid["pearson_r"].max()) + 0.05
        ax.plot([lo, hi], [lo, hi], "--", color="#888888", lw=1, label="Perfect accuracy")

        ax.set_xlabel("Target Pearson r"); ax.set_ylabel("Actual Pearson r")
        ax.legend(fontsize=7, facecolor=AX_BG, edgecolor="#444466", labelcolor=TEXT_COLOR)
        self._style_ax(ax, "Target vs Actual Pearson r")

    def _plot_capacity_ratio_accuracy(self, ax: plt.Axes) -> None:
        """Scatter: target capacity_ratio_input vs realised capacity_ratio."""
        valid = self.df.dropna(subset=["capacity_ratio_input"])
        if valid.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", color=TEXT_COLOR)
            self._style_ax(ax, "Capacity Ratio: Target vs Actual")
            return

        ax.scatter(
            valid["capacity_ratio_input"], valid["capacity_ratio"],
            s=15, alpha=0.6, color=ACCENT, linewidths=0,
        )
        lo = min(valid["capacity_ratio_input"].min(), valid["capacity_ratio"].min()) - 0.02
        hi = max(valid["capacity_ratio_input"].max(), valid["capacity_ratio"].max()) + 0.02
        ax.plot([lo, hi], [lo, hi], "--", color="#888888", lw=1)
        ax.set_xlabel("Target capacity_ratio"); ax.set_ylabel("Actual capacity_ratio")
        self._style_ax(ax, "Capacity Ratio: Target vs Actual")

    def _plot_distribution(self, ax: plt.Axes, field: str, label: str) -> None:
        """KDE + rug distribution of a per-item field, grouped by target_pearson_r."""
        valid = self.df.dropna(subset=["target_pearson_r"])
        r_vals = sorted(valid["target_pearson_r"].unique())
        palette = plt.colormaps["plasma"].resampled(len(r_vals))

        for i, r_val in enumerate(r_vals):
            ids = set(valid[valid["target_pearson_r"] == r_val]["test_id"])
            data = []
            for rec in self._records:
                if rec["test_id"] in ids:
                    data.extend(rec[field])
            if data:
                arr = np.array(data)
                # KDE via seaborn on the axis
                sns.kdeplot(
                    arr, ax=ax, color=palette(i), linewidth=1.5,
                    label=f"r≈{r_val}", fill=True, alpha=0.18,
                )

        ax.set_xlabel(label); ax.set_ylabel("Density")
        ax.legend(fontsize=7, facecolor=AX_BG, edgecolor="#444466", labelcolor=TEXT_COLOR)
        self._style_ax(ax, f"{label} Distribution by target r")

    def _plot_density_cv_by_n(self, ax: plt.Axes) -> None:
        """Box plot of density_cv grouped by (n, target_pearson_r)."""
        valid = self.df.dropna(subset=["target_pearson_r"]).copy()
        valid["group"] = valid["n_label"] + "\n" + valid["target_r_label"]

        order = sorted(valid["group"].unique(), key=lambda s: (
            int(s.split("\n")[0].replace("n=", "")),
            float(s.split("≈")[1]),
        ))

        sns.boxplot(
            data=valid, x="group", y="density_cv", order=order,
            hue="group", legend=False,
            ax=ax, palette="plasma",
            linewidth=0.8, fliersize=2,
        )
        ax.set_xlabel("(n, target r)"); ax.set_ylabel("density_cv")
        ax.tick_params(axis="x", labelsize=6)
        self._style_ax(ax, "Density CV by N and Target Pearson r")

    def _plot_pearson_r_by_n(self, ax: plt.Axes) -> None:
        """Violin plot of realised pearson_r grouped by n for each target_r."""
        valid = self.df.dropna(subset=["target_pearson_r"]).copy()
        sns.violinplot(
            data=valid, x="n_label", y="pearson_r",
            hue="target_r_label", ax=ax,
            palette="cool", linewidth=0.6, cut=0, inner="quartile",
        )
        ax.axhline(0, color="#666666", lw=0.8, linestyle="--")
        ax.set_xlabel("N"); ax.set_ylabel("Actual Pearson r")
        legend = ax.get_legend()
        if legend:
            legend.set_title("Target r", prop={"size": 7})
            plt.setp(legend.get_texts(), color=TEXT_COLOR, fontsize=7)
            plt.setp(legend.get_title(), color=TEXT_COLOR)
            legend.get_frame().set_facecolor(AX_BG)
            legend.get_frame().set_edgecolor("#444466")
        self._style_ax(ax, "Realised Pearson r Distribution by N")

    def _plot_metadata_heatmap(self, ax: plt.Axes) -> None:
        """Correlation heatmap of the numeric metadata columns."""
        cols = ["n", "capacity_ratio", "pearson_r", "density_cv",
                "target_pearson_r", "capacity_ratio_input"]
        sub = self.df[cols].dropna()
        corr = sub.corr()

        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(
            corr, mask=mask, ax=ax,
            cmap="coolwarm", center=0, vmin=-1, vmax=1,
            annot=True, fmt=".2f", annot_kws={"size": 8},
            linewidths=0.5, linecolor="#333355",
            cbar_kws={"shrink": 0.8},
        )
        ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right", fontsize=8)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=8)
        self._style_ax(ax, "Metadata Correlation Heatmap")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Visualize quality of generated knapsack test instances."
    )
    parser.add_argument(
        "--raw", type=Path,
        default=Path(__file__).resolve().parent / "raw",
        help="Directory containing generated JSON instances.",
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path(__file__).resolve().parents[1] / "results" / "quality",
        help="Directory to save the dashboard image.",
    )
    args = parser.parse_args()

    analyzer = TestcaseQualityAnalyzer(args.raw)
    analyzer.print_summary()
    analyzer.plot_all(output_dir=args.output)


if __name__ == "__main__":
    main()
