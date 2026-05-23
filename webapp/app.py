"""Flask webapp entry point for Knapsack Optimization visualization."""

from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, render_template

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from webapp.api.benchmark_api import bp as benchmark_bp
from webapp.api.solver_api import bp as solver_bp
from webapp.api.data_api import bp as data_bp
from webapp.api.runner_api import bp as runner_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )
    app.config["ROOT_DIR"] = str(ROOT_DIR)
    app.config["DATA_RAW_DIR"] = str(ROOT_DIR / "data" / "raw")
    app.config["RESULTS_CSV_DIR"] = str(ROOT_DIR / "results" / "csv")
    app.config["RESULTS_QUALITY_DIR"] = str(ROOT_DIR / "results" / "quality")
    app.config["RESULTS_PLOTS_DIR"] = str(ROOT_DIR / "results" / "plots")
    app.config["SCENARIOS_FILE"] = str(ROOT_DIR / "data" / "test_scenarios.json")

    app.register_blueprint(benchmark_bp, url_prefix="/api/benchmark")
    app.register_blueprint(solver_bp, url_prefix="/api/solver")
    app.register_blueprint(data_bp, url_prefix="/api/data")
    app.register_blueprint(runner_bp, url_prefix="/api/runner")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Knapsack Visualization webapp")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    application = create_app()
    application.run(host=args.host, port=args.port, debug=args.debug)
