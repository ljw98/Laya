"""Laya demo: one state, typed questions, single forward pass."""
import json
import os
import time

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import laya
from laya import Router, load

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL_MODEL = os.path.join(HERE, "models", "laya")


def main() -> None:
    print(f"laya version: {laya.__version__}")
    print("loading local checkpoint ...")
    t0 = time.perf_counter()
    agent = load(LOCAL_MODEL, device="cpu")
    print(f"agent ready in {time.perf_counter() - t0:.1f}s")

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
            "criteria": [
                "not urgent",
                "soon",
                "critical deadline or blocking issue",
            ],
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
    res = agent.predict(state, questions)
    dt = (time.perf_counter() - t1) * 1000

    print(f"\n=== English state ({dt:.0f} ms) ===")
    for qid, ans in res["answers"].items():
        print(f"  {qid}: {json.dumps(ans, ensure_ascii=False)}")

    # Built-in presets: quick triage
    print("\n=== Preset: triage_questions ===")
    res_triage = agent.predict(
        {"message": "My payment failed twice and I need this fixed today!"},
        laya.triage_questions(),
    )
    for qid, ans in res_triage["answers"].items():
        print(f"  {qid}: {json.dumps(ans, ensure_ascii=False)}")

    print("\nDONE")


if __name__ == "__main__":
    main()
