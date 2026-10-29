"""Resume and finish the post-P3 study phases in a single audited sequence.

This helper is intentionally conservative: it waits for P3's hard completion assertion, runs GPU
phases one at a time, records each phase log, and stops on the first non-zero exit.  Every phase has
its own resume flag, so an interrupted continuation can be restarted safely.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PYTHON = Path(sys.executable)
P3_LOG = ROOT / "runs" / "p3_sparse_curve_graph_gpu_grouped.log"
P3_RESULT = ROOT / "artifacts" / "metrics" / "sparse_curve_subject_metrics.csv"


def wait_for_p3():
    print("waiting for P3 completion assertion", flush=True)
    while True:
        text = P3_LOG.read_text(encoding="utf-8", errors="replace") if P3_LOG.exists() else ""
        if "ASSERTION FAILED" in text or "Traceback" in text:
            raise RuntimeError("P3 log contains a failure; continuation stopped")
        rows = 0
        if P3_RESULT.exists():
            try:
                rows = len(pd.read_csv(P3_RESULT))
            except Exception:
                rows = 0
        if "ASSERTION PASSED: 43 participants x 16 k x 4 lambda" in text and rows == 43 * 16 * 4:
            print(f"P3 complete with {rows} rows", flush=True)
            return
        print(f"P3 still running; current rows={rows}", flush=True)
        time.sleep(30)


def run_phase(name, args):
    log = ROOT / "runs" / f"{name}_orchestrated.log"
    print(f"starting {name}: {' '.join(args)}", flush=True)
    with log.open("w", encoding="utf-8") as fh:
        result = subprocess.run([str(PYTHON), *args], cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT,
                                 check=False)
    print(f"{name} exit={result.returncode}; log={log}", flush=True)
    if result.returncode != 0:
        raise RuntimeError(f"{name} failed with exit code {result.returncode}")


def main():
    wait_for_p3()

    run_phase("p5_statistics", ["scripts/28_statistics.py"])

    master = pd.read_csv(ROOT / "artifacts" / "statistics" / "master_statistics.csv")
    kstar_rows = master[(master.quantity == "k_star")
                        & (master["lambda"].astype(float).sub(0.5).abs() < 1e-8)
                        & (master.margin.astype(float).sub(0.02).abs() < 1e-8)
                        & master["k_star_found"].astype(str).str.lower().eq("true")]
    k_values = {4, 6, 8}
    k_star = 0
    if not kstar_rows.empty:
        k_star = int(kstar_rows.iloc[0].estimate)
        if 1 <= k_star <= 16:
            k_values.add(k_star)
    k_arg = ",".join(str(k) for k in sorted(k_values))
    p4_args = [
        "scripts/27_selection_baselines.py", "--device", "cuda", "--workers", "2",
        "--fit-workers", "4", "--k-values", k_arg, "--n-random", "100",
        "--n-random-at-k-star", "500", "--srcfa-lambda", "0.5", "--resume",
    ]
    if k_star:
        p4_args.extend(["--k-star", str(k_star)])
    run_phase("p4_selection_baselines", p4_args)

    run_phase("p7_cross_session", ["scripts/30_cross_session.py", "--device", "cuda", "--resume"])
    run_phase("p8_faithfulness", ["scripts/31_faithfulness.py", "--device", "cuda",
                                  "--srcfa-lambda", "0.0", "--fit-workers", "4", "--resume"])
    run_phase("p9_db5", ["scripts/34_db5_replication.py", "--device", "cuda", "--resume"])
    run_phase("p11_bipolar", ["scripts/36_bipolar_sensitivity.py", "--device", "cuda",
                              "--k-workers", "4", "--resume"])
    run_phase("strict_verification", ["scripts/16_verify_results.py"])
    run_phase("final_report", ["scripts/41_generate_study_report.py"])
    print("ALL_REQUIRED_STUDY_PHASES_COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ORCHESTRATOR FAILED: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)
