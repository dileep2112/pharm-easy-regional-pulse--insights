"""
run_pipeline.py -- PharmEasy Regional Pulse, one-command end-to-end run.

Runs every stage in order, each consuming the previous stage's output,
so a fresh clone only needs:

    pip install -r requirements.txt
    python run_pipeline.py
    streamlit run app.py

This does not replace the individual scripts (generate_dataset.py,
clean_data.py, build_db.py, queries.py, metrics_engine.py,
draft_report.py, review_gate.py) -- it calls each of their `main`
behavior in sequence via subprocess, printing a clear banner between
stages, and stops immediately if any stage fails.
"""

import subprocess
import sys

STAGES = [
    ("Part 1 - generate raw dataset", [sys.executable, "generate_dataset.py"]),
    ("Part 1 - clean data + validate schema", [sys.executable, "clean_data.py"]),
    ("Part 2 - build SQLite database", [sys.executable, "build_db.py"]),
    ("Part 2 - JOIN validation + region/month metrics", [sys.executable, "queries.py"]),
    ("Part 2 - significance flagging + state persistence", [sys.executable, "metrics_engine.py"]),
    ("Part 3 - draft CII report for flagged regions", [sys.executable, "draft_report.py"]),
    ("Part 3 - review-gate test harness (writes audit_log.jsonl)", [sys.executable, "review_gate.py"]),
]


def run():
    for label, cmd in STAGES:
        banner = f"=== {label} ==="
        print("\n" + banner)
        print("-" * len(banner))
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"\nPipeline stopped: '{' '.join(cmd)}' failed (exit code {result.returncode}).")
            sys.exit(result.returncode)

    print("\n" + "=" * 60)
    print("Pipeline complete. Every stage ran on the previous stage's")
    print("output: raw data -> clean data -> pharmeasy.db -> verified")
    print("metrics -> flags -> CII draft -> reviewed/audit-logged draft.")
    print("Next: streamlit run app.py")
    print("=" * 60)


if __name__ == "__main__":
    run()
