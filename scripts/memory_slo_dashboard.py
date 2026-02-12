#!/usr/bin/env python3
"""Build memory SLO metrics snapshot for reporting."""

import json
import os
import glob
from datetime import datetime

WORKSPACE = "/Users/ellisbot/.openclaw/workspace"
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
HEALTH_PATH = os.path.join(MEMORY_DIR, "health.json")
INTEGRITY_DIR = os.path.join(WORKSPACE, "data", "integrity_reports")
MISSES_PATH = os.path.join(MEMORY_DIR, "memory_miss_incidents.md")
OUT_PATH = os.path.join(MEMORY_DIR, "slo_status.json")


def load_health():
    if not os.path.exists(HEALTH_PATH):
        return {}
    try:
        with open(HEALTH_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def latest_integrity_report():
    files = sorted(glob.glob(os.path.join(INTEGRITY_DIR, "memory_integrity_*.json")))
    if not files:
        return None
    p = files[-1]
    try:
        with open(p, "r") as f:
            data = json.load(f)
        data["path"] = p
        return data
    except Exception:
        return None


def miss_incident_count():
    if not os.path.exists(MISSES_PATH):
        return 0
    with open(MISSES_PATH, "r") as f:
        text = f.read()
    # count section headers that look like incidents
    return max(0, text.count("## 20"))


def evaluate_slo(health, integrity, incidents):
    # Support both health.json schemas:
    # A) {tests_passed, tests_total, all_pass}
    # B) {checks: {search_tests: {passed,total}}, all_pass}
    tests_passed = int(health.get("tests_passed", 0))
    tests_total = int(health.get("tests_total", 0))
    if tests_total == 0:
        search = (health.get("checks") or {}).get("search_tests") or {}
        tests_passed = int(search.get("passed", 0))
        tests_total = int(search.get("total", 0))
    all_pass = bool(health.get("all_pass", False))
    missing_count = int((integrity or {}).get("missing_count", 9999)) if integrity else 9999

    # Simple SLO gates
    slo = {
        "search_verification": "pass" if all_pass and tests_total >= 5 else "fail",
        "capture_integrity": "pass" if missing_count == 0 else "fail",
        "incident_backlog": "pass" if incidents <= 3 else "warn",
    }

    overall = "GREEN"
    if "fail" in slo.values():
        overall = "RED"
    elif "warn" in slo.values():
        overall = "YELLOW"

    return {
        "overall": overall,
        "tests_passed": tests_passed,
        "tests_total": tests_total,
        "missing_count": missing_count,
        "incidents": incidents,
        "slo": slo,
    }


def main():
    health = load_health()
    integrity = latest_integrity_report()
    incidents = miss_incident_count()
    status = evaluate_slo(health, integrity, incidents)

    payload = {
        "timestamp": datetime.now().isoformat(),
        "health": {
            "tests_passed": status["tests_passed"],
            "tests_total": status["tests_total"],
        },
        "integrity": {
            "missing_count": status["missing_count"],
            "report": (integrity or {}).get("path"),
        },
        "incidents": status["incidents"],
        "slo": status["slo"],
        "overall": status["overall"],
    }

    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
