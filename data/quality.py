"""Quality-assurance plots for generated knapsack benchmark instances.

Each plot is saved as a separate PNG file for clarity.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import norm as _norm

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ── Design tokens ─────────────────────────────────────────────────────────────
FIG_BG   = "#0f0f1a"
AX_BG    = "#16213e"
GRID_CLR = "#2a2a4a"
TEXT     = "#dde1f0"
MUTED    = "#8890b0"
ACCENT   = ["#7b68ee", "#00d4aa", "#ff6b6b", "#ffd166", "#06d6a0",
            "#ef476f", "#118ab2", "#fca311"]
DIAG_CLR = "#ffcc44"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.labelsize": 10, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "legend.fontsize": 9,
})


class TestcaseQualityAnalyzer:
    """Load benchmark instances and produce individual QA plot files."""

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
                "test_id":               raw["test_id"],
                "capacity":              raw["capacity"],
                "n":                     int(meta.get("n", 0)),
                "n_anchor":              int(meta.get("n_anchor", meta.get("n", 0))),
                "n_actual":              int(meta.get("n_actual", meta.get("n", 0))),
                "capacity_ratio":        float(meta.get("capacity_ratio", 0)),
                "capacity_ratio_anchor": float(meta.get("capacity_ratio_anchor",
                                               meta.get("capacity_ratio_input", 0))),
                "capacity_ratio_actual": float(meta.get("capacity_ratio_actual",
                                               meta.get("capacity_ratio", 0))),
                "pearson_r":             float(meta.get("pearson_r", 0)),
                "target_pearson_r":      float(meta.get("target_pearson_r", float("nan"))),
                "density_cv":            float(meta.get("density_cv", 0)),
                "max_weight":            int(meta.get("max_weight", 0)),
                "seed":                  int(meta.get("seed", 0)),
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
        return pd.DataFrame(rows)

    # ── Styling ───────────────────────────────────────────────────────────────

    def _new_fig(self, w=9, h=6):
        fig, ax = plt.subplots(figsize=(w, h), facecolor=FIG_BG)
        return fig, ax

    def _style(self, ax, title="", xlabel="", ylabel=""):
        ax.set_facecolor(AX_BG)
        ax.set_title(title, color=TEXT, pad=10)
        ax.set_xlabel(xlabel, color=MUTED)
        ax.set_ylabel(ylabel, color=MUTED)
        ax.tick_params(colors=MUTED)
        ax.grid(color=GRID_CLR, lw=0.5, ls="--", alpha=0.6)
        ax.set_axisbelow(True)
        for sp in ax.spines.values():
            sp.set_edgecolor(GRID_CLR)

    def _legend(self, ax, **kw):
        ax.legend(facecolor=AX_BG, edgecolor=GRID_CLR, labelcolor=TEXT,
                  framealpha=0.9, **kw)

    def _save(self, fig, out_dir: Path, name: str):
        path = out_dir / name
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=FIG_BG)
        plt.close(fig)
        print(f"  -> {path}")

    # ── Individual plot methods ───────────────────────────────────────────────

    def _plot_gaussian_hist(self, out_dir, col_actual, col_anchor, title, xlabel, filename):
        fig, ax = self._new_fig(10, 5.5)
        anchors = sorted(self.df[col_anchor].unique())

        for i, anchor in enumerate(anchors):
            sub = self.df[self.df[col_anchor] == anchor][col_actual]
            if sub.empty or sub.std() == 0:
                continue
            color = ACCENT[i % len(ACCENT)]
            label = f"anchor={anchor:g}"

            sns.histplot(sub, ax=ax, kde=False, stat="density",
                         color=color, alpha=0.3, bins="auto",
                         edgecolor=AX_BG, linewidth=0.4, label=label)

            mu, sigma = sub.mean(), sub.std()
            xs = np.linspace(sub.min() - sigma, sub.max() + sigma, 200)
            ax.plot(xs, _norm.pdf(xs, mu, sigma), color=color, lw=2.5)
            ax.axvline(anchor, color=color, ls="--", lw=1.2, alpha=0.7)

        self._legend(ax)
        self._style(ax, title, xlabel, "Density")
        self._save(fig, out_dir, filename)

    def _plot_scatter_anchor_vs_actual(self, out_dir, col_actual, col_anchor,
                                       title, label, filename):
        fig, ax = self._new_fig(8, 6)
        ax.scatter(self.df[col_anchor], self.df[col_actual],
                   s=18, alpha=0.55, color=ACCENT[0], linewidths=0)

        lo = min(self.df[col_anchor].min(), self.df[col_actual].min())
        hi = max(self.df[col_anchor].max(), self.df[col_actual].max())
        margin = (hi - lo) * 0.05 if hi > lo else 1
        ax.plot([lo - margin, hi + margin], [lo - margin, hi + margin],
                "--", color=DIAG_CLR, lw=1.5, label="y = x (no jitter)")

        self._legend(ax)
        self._style(ax, title, f"{label} (anchor)", f"{label} (actual)")
        self._save(fig, out_dir, filename)

    def _plot_pearson_accuracy(self, out_dir, filename):
        fig, ax = self._new_fig(9, 6)
        df = self.df.dropna(subset=["target_pearson_r"])
        n_anchors = sorted(df["n_anchor"].unique())
        cmap = plt.colormaps["cool"].resampled(len(n_anchors))

        for i, na in enumerate(n_anchors):
            sub = df[df["n_anchor"] == na]
            ax.scatter(sub["target_pearson_r"], sub["pearson_r"],
                       s=22, alpha=0.75, color=cmap(i), linewidths=0.3,
                       edgecolors=AX_BG, label=f"n={na}")

        rng = [df["target_pearson_r"].min() - 0.05,
               df["target_pearson_r"].max() + 0.05]
        ax.plot(rng, rng, "--", color=DIAG_CLR, lw=1.5, label="Perfect accuracy")
        ax.text(rng[1] - 0.02, rng[1] + 0.02, "y=x", color=DIAG_CLR, fontsize=9)

        self._legend(ax, fontsize=8)
        self._style(ax, "Target vs Actual Pearson r (colored by n)",
                    "Target Pearson r", "Actual Pearson r")
        self._save(fig, out_dir, filename)

    # ── Public API ────────────────────────────────────────────────────────────

    def plot_all(self, output_dir: str | Path | None = None) -> None:
        """Generate all QA plots as separate files."""
        plt.style.use("dark_background")
        out = Path(output_dir) if output_dir else Path("results/quality")
        out.mkdir(parents=True, exist_ok=True)

        print("Generating quality plots:")

        # 1) Gaussian histogram: n_actual
        self._plot_gaussian_hist(
            out, "n_actual", "n_anchor",
            "n_actual Distribution (Gaussian jitter around anchor)",
            "n_actual",
            "01_hist_n_actual.png",
        )

        # 2) Gaussian histogram: capacity_ratio_actual
        self._plot_gaussian_hist(
            out, "capacity_ratio_actual", "capacity_ratio_anchor",
            "capacity_ratio_actual Distribution (Gaussian jitter)",
            "capacity_ratio_actual",
            "02_hist_ratio_actual.png",
        )

        # 3) Gaussian histogram: pearson_r actual
        self._plot_gaussian_hist(
            out, "pearson_r", "target_pearson_r",
            "Actual Pearson r Distribution (around target)",
            "pearson_r (actual)",
            "03_hist_pearson_actual.png",
        )

        # 4) Scatter: n anchor vs n actual
        self._plot_scatter_anchor_vs_actual(
            out, "n_actual", "n_anchor",
            "n: Anchor vs Actual (jitter spread)", "n",
            "04_scatter_n_jitter.png",
        )

        # 5) Scatter: ratio anchor vs ratio actual
        self._plot_scatter_anchor_vs_actual(
            out, "capacity_ratio_actual", "capacity_ratio_anchor",
            "Capacity Ratio: Anchor vs Actual (jitter spread)", "capacity_ratio",
            "05_scatter_ratio_jitter.png",
        )

        # 6) Scatter: target pearson_r vs actual pearson_r
        self._plot_pearson_accuracy(out, "06_scatter_pearson_accuracy.png")

        print(f"Done. {6} plots saved to {out}")

    def print_summary(self) -> None:
        df = self.df
        print("=" * 60)
        print("  TESTCASE QUALITY SUMMARY")
        print("=" * 60)
        print(f"  Total instances : {len(df)}")
        print(f"  n anchors       : {sorted(df['n_anchor'].unique())}")
        print(f"  Target r values : {sorted(df['target_pearson_r'].dropna().unique())}")
        print(f"  CR anchors      : {sorted(df['capacity_ratio_anchor'].unique())}")
        print()
        key = ["n_actual", "capacity_ratio_actual", "pearson_r", "density_cv"]
        print(df[key].describe().round(4).to_string())
        print()
        valid = df.dropna(subset=["target_pearson_r"]).copy()
        valid["r_err"] = (valid["pearson_r"] - valid["target_pearson_r"]).abs()
        print("  Pearson-r accuracy:")
        print(valid.groupby("target_pearson_r")["r_err"]
              .describe().round(4).to_string())
        print("=" * 60)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--raw", type=Path,
                   default=Path(__file__).resolve().parent / "raw")
    p.add_argument("--output", type=Path,
                   default=Path(__file__).resolve().parents[1] / "results" / "quality")
    args = p.parse_args()

    analyzer = TestcaseQualityAnalyzer(args.raw)
    analyzer.print_summary()
    analyzer.plot_all(output_dir=args.output)


if __name__ == "__main__":
    main()
