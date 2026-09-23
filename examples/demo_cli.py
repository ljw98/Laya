"""Laya CLI demo: load local checkpoint and run typed questions in one forward pass.

Usage:
    python examples/demo_cli.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "laya-main" / "models" / "laya"
sys.path.insert(0, str(ROOT / "laya-main"))


def main() -> None:
    import laya

    print(f"laya {laya.__version__}")
    print(f"loading {MODEL_DIR} ...")
    t0 = time.perf_counter()
    agent = laya.load(str(MODEL_DIR), device="cpu")
    print(f"ready in {time.perf_counter() - t0:.1f}s")

    state = {
        "from": "user@acme.com",
        "subject": "Duplicate charge on invoice #4411",
        "body": (
            "Hi, we were billed twice for March. "
            "Please refund the duplicate today or we will cancel our plan."
        ),
    }
    questions = {
        "department": {
            "type": "choice",
            "instructions": "Which department should handle this request?",
            "criteria": {
                "billing": "invoices, payments, refunds",
                "technical": "bugs, outages, system errors",
                "sales": "pricing, new contracts",
                "other": "everything else",
            },
        },
        "urgency": {
            "type": "score",
            "instructions": "How urgent is this request?",
            "criteria": ["not urgent", "soon", "critical deadline or blocking issue"],
        },
        "churn_risk": {
            "type": "noul",
            "instructions": "Does the user threaten to cancel or leave?",
        },
        "refund_requested": {
            "type": "noul",
            "instructions": "Does the user explicitly request a refund?",
        },
    }

    t1 = time.perf_counter()
    result = agent.predict(state, questions)
    ms = (time.perf_counter() - t1) * 1000

    print(f"\n=== predict ({ms:.0f} ms) ===")
    for qid, ans in result["answers"].items():
        print(f"  {qid}: {json.dumps(ans, ensure_ascii=False)}")
    print("DONE")


if __name__ == "__main__":
    main()
