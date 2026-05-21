"""Analyze and visualize the quality of generated knapsack benchmark instances."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ── Design tokens ─────────────────────────────────────────────────────────────
FIG_BG     = "#0f0f1a"
AX_BG      = "#16213e"
GRID_COLOR = "#2a2a4a"
TEXT       = "#dde1f0"
MUTED      = "#8890b0"
PALETTE    = ["#7b68ee", "#00d4aa", "#ff6b6b"]   # r=0 / r=0.5 / r=0.95
DIAG_CLR   = "#ffcc44"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
})


class TestcaseQualityAnalyzer:
    """Load generated benchmark instances and produce a quality report."""

    def __init__(self, raw_dir: str | Path) -> None:
        self.raw_dir = Path(raw_dir)
        self._records: List[Dict[str, Any]] = self._load_all()
        self.df: pd.DataFrame = self._build_dataframe()

    # ── Loaders ───────────────────────────────────────────────────────────────

    def _load_all(self) -> List[Dict[str, Any]]:
        files = sorted(self.raw_dir.glob("*.json"))
        if not files:
            raise FileNotFoundError(f"No JSON files in {self.raw_dir}")
        records = []
        for path in files:
            raw = json.loads(path.read_text(encoding="utf-8"))
            meta = raw.get("metadata", {})
            rec = {
                "test_id":              raw["test_id"],
                "capacity":             raw["capacity"],
                "n":                    int(meta.get("n", 0)),
                "capacity_ratio":       float(meta.get("capacity_ratio", 0)),
                "pearson_r":            float(meta.get("pearson_r", 0)),
                "density_cv":           float(meta.get("density_cv", 0)),
                "target_pearson_r":     float(meta.get("target_pearson_r", float("nan"))),
                "capacity_ratio_input": float(meta.get("capacity_ratio_input", float("nan"))),
                "max_weight":           int(meta.get("max_weight", 0)),
                "seed":                 int(meta.get("seed", 0)),
                "instance_seed":        int(meta.get("instance_seed", meta.get("seed", 0))),
            }
            items = raw.get("items", [])
            rec["weights"]   = [it["weight"] for it in items]
            rec["values"]    = [it["value"]  for it in items]
            rec["densities"] = [
                it["value"] / it["weight"] if it["weight"] else 0.0
                for it in items
            ]
            records.append(rec)
        return records

    def _build_dataframe(self) -> pd.DataFrame:
        rows = [
            {k: v for k, v in r.items() if k not in ("weights", "values", "densities")}
            for r in self._records
        ]
        df = pd.DataFrame(rows)
        df["n_label"] = "n=" + df["n"].astype(str)
        r_unique = sorted(df["target_pearson_r"].dropna().unique())
        self._r_color = {rv: PALETTE[i % len(PALETTE)] for i, rv in enumerate(r_unique)}
        df["r_label"] = df["target_pearson_r"].map(
            lambda x: f"r={x:g}" if not np.isnan(x) else "?"
        )
        return df

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _style(self, ax: plt.Axes, title: str, xlabel: str = "", ylabel: str = "") -> None:
        ax.set_facecolor(AX_BG)
        ax.set_title(title, color=TEXT, pad=8, fontweight="bold")
        ax.set_xlabel(xlabel, color=MUTED)
        ax.set_ylabel(ylabel, color=MUTED)
        ax.tick_params(colors=MUTED)
        ax.grid(color=GRID_COLOR, linewidth=0.5, linestyle="--", alpha=0.6)
        ax.set_axisbelow(True)
        for sp in ax.spines.values():
            sp.set_edgecolor(GRID_COLOR)

    def _legend(self, ax: plt.Axes, **kw) -> None:
        leg = ax.legend(
            facecolor=AX_BG, edgecolor=GRID_COLOR, labelcolor=TEXT,
            framealpha=0.9, **kw
        )
        if leg:
            leg.get_frame().set_linewidth(0.5)

    def _r_items(self) -> list[tuple[float, str, str]]:
        """Return (r_val, label, color) sorted by r_val."""
        return [
            (rv, f"r={rv:g}", c)
            for rv, c in sorted(self._r_color.items())
        ]

    # ── Individual plots ──────────────────────────────────────────────────────

    def _plot_scatter_by_r(self, ax: plt.Axes) -> None:
        """Weight vs Value faceted by target Pearson r (one colour per level)."""
        rng = np.random.default_rng(0)
        valid = self.df.dropna(subset=["target_pearson_r"])

        for rv, label, color in self._r_items():
            ids = set(valid[valid["target_pearson_r"] == rv]["test_id"])
            # Sample ≤2 instances per r-level to avoid overplotting
            sampled_ids = set(list(ids)[:2])
            ws, vs = [], []
            for rec in self._records:
                if rec["test_id"] in sampled_ids:
                    ws.extend(rec["weights"])
                    vs.extend(rec["values"])
            if ws:
                ax.scatter(ws, vs, s=8, alpha=0.35, color=color,
                           linewidths=0, label=label, rasterized=True)
                # Trend line
                p = np.polyfit(ws, vs, 1)
                xs = np.array([min(ws), max(ws)])
                ax.plot(xs, np.polyval(p, xs), color=color, lw=1.5, alpha=0.9)

        self._legend(ax, loc="upper left", markerscale=2)
        self._style(ax, "Weight vs Value by Target r",
                    xlabel="Weight", ylabel="Value")

    def _plot_target_vs_actual_r(self, ax: plt.Axes) -> None:
        """Actual Pearson r vs target, coloured by n."""
        valid = self.df.dropna(subset=["target_pearson_r"])
        n_vals = sorted(valid["n"].unique())
        cmap = plt.colormaps["cool"].resampled(len(n_vals))

        for i, nv in enumerate(n_vals):
            sub = valid[valid["n"] == nv]
            ax.scatter(sub["target_pearson_r"], sub["pearson_r"],
                       s=22, alpha=0.75, color=cmap(i),
                       linewidths=0.4, edgecolors=AX_BG, label=f"n={nv}")

        lo = valid[["target_pearson_r", "pearson_r"]].min().min() - 0.05
        hi = valid[["target_pearson_r", "pearson_r"]].max().max() + 0.05
        ax.plot([lo, hi], [lo, hi], "--", color=DIAG_CLR, lw=1.2,
                label="Perfect accuracy", zorder=5)
        ax.text(hi - 0.02, hi + 0.02, "y=x", color=DIAG_CLR,
                fontsize=7, ha="right")

        self._legend(ax, loc="upper left")
        self._style(ax, "Target vs Actual Pearson r",
                    xlabel="Target r", ylabel="Actual r")

    def _plot_r_error_by_n(self, ax: plt.Axes) -> None:
        """Mean absolute error |actual r − target r| grouped by n."""
        valid = self.df.dropna(subset=["target_pearson_r"]).copy()
        valid["r_err"] = (valid["pearson_r"] - valid["target_pearson_r"]).abs()

        for rv, label, color in self._r_items():
            sub = valid[valid["target_pearson_r"] == rv]
            grouped = sub.groupby("n")["r_err"].mean().reset_index()
            ax.plot(grouped["n"], grouped["r_err"], "o-", color=color,
                    lw=1.5, ms=5, label=label)

        ax.axhline(0, color=DIAG_CLR, lw=0.8, linestyle="--", alpha=0.5)
        self._legend(ax)
        self._style(ax, "|Actual r − Target r| by N",
                    xlabel="n (items)", ylabel="Mean absolute error")

    def _plot_distributions(self, ax_w: plt.Axes, ax_v: plt.Axes,
                            ax_d: plt.Axes) -> None:
        """KDE distributions for weight, value, density grouped by target r."""
        valid = self.df.dropna(subset=["target_pearson_r"])

        for field, ax, label in [
            ("weights",   ax_w, "Weight"),
            ("values",    ax_v, "Value"),
            ("densities", ax_d, "Density v/w"),
        ]:
            for rv, lbl, color in self._r_items():
                ids = set(valid[valid["target_pearson_r"] == rv]["test_id"])
                data = []
                for rec in self._records:
                    if rec["test_id"] in ids:
                        data.extend(rec[field])
                if data:
                    sns.kdeplot(np.array(data), ax=ax, color=color,
                                lw=2, label=lbl, fill=True, alpha=0.15)
            self._legend(ax)
            self._style(ax, f"{label} Distribution by r",
                        xlabel=label, ylabel="Density")

    def _plot_density_cv(self, ax: plt.Axes) -> None:
        """Strip + box plot of density_cv per n, split by target r."""
        valid = self.df.dropna(subset=["target_pearson_r"]).copy()
        n_order = [f"n={v}" for v in sorted(valid["n"].unique())]

        sns.boxplot(
            data=valid, x="n_label", y="density_cv", hue="r_label",
            order=n_order, ax=ax,
            palette={lbl: c for _, lbl, c in self._r_items()},
            width=0.55, linewidth=0.8, fliersize=0,
            boxprops=dict(alpha=0.5),
        )
        sns.stripplot(
            data=valid, x="n_label", y="density_cv", hue="r_label",
            order=n_order, ax=ax,
            palette={lbl: c for _, lbl, c in self._r_items()},
            dodge=True, size=3.5, alpha=0.7, linewidth=0,
            legend=False,
        )
        # Keep only the boxplot legend entry
        handles, labels = ax.get_legend_handles_labels()
        half = len(handles) // 2
        ax.legend(handles[:half], labels[:half],
                  facecolor=AX_BG, edgecolor=GRID_COLOR, labelcolor=TEXT,
                  framealpha=0.9, fontsize=8, title="Target r",
                  title_fontsize=8)
        self._style(ax, "Density CV by N and Target r",
                    xlabel="N", ylabel="density_cv")

    def _plot_heatmap(self, ax: plt.Axes) -> None:
        """Correlation heatmap of key numeric metadata."""
        cols = ["n", "capacity_ratio", "pearson_r", "density_cv",
                "target_pearson_r", "capacity_ratio_input"]
        sub = self.df[cols].dropna()
        corr = sub.corr(method="spearman")
        mask = np.triu(np.ones_like(corr, dtype=bool), k=1)

        sns.heatmap(
            corr, mask=mask, ax=ax,
            cmap="coolwarm", center=0, vmin=-1, vmax=1,
            annot=True, fmt=".2f", annot_kws={"size": 8, "color": TEXT},
            linewidths=0.4, linecolor=GRID_COLOR,
            cbar_kws={"shrink": 0.75, "label": "Spearman ρ"},
        )
        ax.set_xticklabels(ax.get_xticklabels(),
                           rotation=35, ha="right", fontsize=7, color=TEXT)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0,
                           fontsize=7, color=TEXT)
        cbar = ax.collections[0].colorbar
        cbar.ax.tick_params(labelsize=7, colors=MUTED)
        cbar.set_label("Spearman ρ", color=MUTED, fontsize=8)
        self._style(ax, "Metadata Correlation (Spearman ρ)")

    def _plot_capacity_accuracy(self, ax: plt.Axes) -> None:
        """Actual capacity ratio vs target — should cluster on y=x."""
        valid = self.df.dropna(subset=["capacity_ratio_input"])
        for rv, lbl, color in self._r_items():
            sub = valid[valid["target_pearson_r"] == rv]
            if not sub.empty:
                ax.scatter(sub["capacity_ratio_input"], sub["capacity_ratio"],
                           s=20, alpha=0.7, color=color, linewidths=0,
                           label=lbl)
        lo, hi = 0.0, 1.0
        ax.plot([lo, hi], [lo, hi], "--", color=DIAG_CLR, lw=1.2, zorder=5)
        self._legend(ax)
        self._style(ax, "Capacity Ratio: Target vs Actual",
                    xlabel="Target ratio", ylabel="Actual ratio")

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def plot_all(self, output_dir: str | Path | None = None) -> None:
        """Render the full 9-subplot quality dashboard."""
        plt.style.use("dark_background")
        fig = plt.figure(figsize=(24, 20), facecolor=FIG_BG)
        fig.suptitle(
            "Knapsack Testcase Quality Dashboard",
            fontsize=16, color=TEXT, fontweight="bold", y=0.985,
        )

        gs = gridspec.GridSpec(
            3, 3, figure=fig,
            hspace=0.44, wspace=0.33,
            left=0.06, right=0.97, top=0.94, bottom=0.05,
        )
        ax_sc  = fig.add_subplot(gs[0, 0])
        ax_rr  = fig.add_subplot(gs[0, 1])
        ax_err = fig.add_subplot(gs[0, 2])
        ax_w   = fig.add_subplot(gs[1, 0])
        ax_v   = fig.add_subplot(gs[1, 1])
        ax_d   = fig.add_subplot(gs[1, 2])
        ax_cv  = fig.add_subplot(gs[2, 0:2])   # wide
        ax_cap = fig.add_subplot(gs[2, 2])

        # Placeholder for heatmap — share gs[2,2] → move heatmap to separate figure
        self._plot_scatter_by_r(ax_sc)
        self._plot_target_vs_actual_r(ax_rr)
        self._plot_r_error_by_n(ax_err)
        self._plot_distributions(ax_w, ax_v, ax_d)
        self._plot_density_cv(ax_cv)
        self._plot_capacity_accuracy(ax_cap)

        if output_dir:
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            p = out / "quality_dashboard.png"
            fig.savefig(p, dpi=150, bbox_inches="tight", facecolor=FIG_BG)
            print(f"Dashboard -> {p}")

        plt.show()

        # --- Separate heatmap figure ---
        fig2, ax_hm = plt.subplots(figsize=(8, 7), facecolor=FIG_BG)
        fig2.patch.set_facecolor(FIG_BG)
        self._plot_heatmap(ax_hm)
        fig2.suptitle("Metadata Correlation", color=TEXT, fontsize=13,
                      fontweight="bold")
        if output_dir:
            p2 = out / "quality_heatmap.png"
            fig2.savefig(p2, dpi=150, bbox_inches="tight", facecolor=FIG_BG)
            print(f"Heatmap    -> {p2}")
        plt.show()

    # ── Summary ───────────────────────────────────────────────────────────────

    def print_summary(self) -> None:
        print("=" * 60)
        print("  TESTCASE QUALITY SUMMARY")
        print("=" * 60)
        print(f"  Total instances : {len(self.df)}")
        print(f"  n values        : {sorted(self.df['n'].unique())}")
        print(f"  Target r values : {sorted(self.df['target_pearson_r'].dropna().unique())}")
        print(f"  Capacity ratios : {sorted(self.df['capacity_ratio_input'].dropna().unique())}")
        print()
        print(self.df[["n", "pearson_r", "density_cv", "capacity_ratio"]]
              .describe().round(4).to_string())
        print()
        valid = self.df.dropna(subset=["target_pearson_r"]).copy()
        valid["r_err"] = (valid["pearson_r"] - valid["target_pearson_r"]).abs()
        print("  Pearson-r accuracy (mean |error|):")
        print(valid.groupby("target_pearson_r")["r_err"]
              .describe().round(4).to_string())
        print("=" * 60)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw", type=Path,
        default=Path(__file__).resolve().parent / "raw",
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path(__file__).resolve().parents[1] / "results" / "quality",
    )
    args = parser.parse_args()

    analyzer = TestcaseQualityAnalyzer(args.raw)
    analyzer.print_summary()
    analyzer.plot_all(output_dir=args.output)


if __name__ == "__main__":
    main()
