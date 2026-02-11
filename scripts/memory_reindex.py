#!/usr/bin/env python3
"""Memory Re-Index — Run qmd update/embed and verify with search tests."""

import json
import os
import subprocess
import sys
from datetime import datetime

QMD_BIN = "/Users/ellisbot/.bun/bin/qmd"
WORKSPACE = "/Users/ellisbot/.openclaw/workspace"
HEALTH_FILE = os.path.join(WORKSPACE, "memory", "health.json")

SEARCH_TESTS = [
    ("Card Plug margin", ["40%"]),
    ("brevity direct", ["direct", "brevity"]),
    ("Codex Opus", ["Codex", "Opus"]),
    ("ROAS breakeven", ["3.0", "ROAS"]),
    ("FIX IMMEDIATELY memory broken", ["FIX", "fix", "IMMEDIATELY", "immediately"]),
]


def run_cmd(args, cwd=WORKSPACE):
    """Run a command and return (returncode, stdout, stderr)."""
    result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, timeout=120)
    return result.returncode, result.stdout, result.stderr


def run_search(query):
    """Run qmd search (BM25, fast) with more results."""
    rc, stdout, stderr = run_cmd([QMD_BIN, "search", query, "-n", "10"])
    return stdout + stderr


def run_tests():
    """Run all search tests. Returns list of (query, expected, passed, output)."""
    results = []
    for query, expected_any in SEARCH_TESTS:
        output = run_search(query)
        passed = any(exp.lower() in output.lower() for exp in expected_any)
        results.append((query, expected_any, passed, output[:200]))
    return results


def update_health(test_results, reindex_ok):
    """Write health.json with results."""
    os.makedirs(os.path.dirname(HEALTH_FILE), exist_ok=True)
    passed = sum(1 for _, _, p, _ in test_results if p)
    total = len(test_results)
    health = {
        "timestamp": datetime.now().isoformat(),
        "reindex_ok": reindex_ok,
        "tests_passed": passed,
        "tests_total": total,
        "all_pass": passed == total,
        "details": [
            {"query": q, "expected": e, "passed": p}
            for q, e, p, _ in test_results
        ],
    }
    with open(HEALTH_FILE, "w") as f:
        json.dump(health, f, indent=2)
    return health


def main():
    print("🔄 Memory Re-Index")
    print("=" * 40)

    # Step 1: qmd update
    print("\n1. Running qmd update...")
    rc, stdout, stderr = run_cmd([QMD_BIN, "update"])
    if rc != 0:
        print(f"   ⚠️  qmd update returned {rc}")
        print(f"   {stderr[:200]}")
    else:
        print(f"   ✅ qmd update complete")
    if stdout.strip():
        print(f"   {stdout.strip()[:200]}")

    # Step 2: qmd embed
    print("\n2. Running qmd embed...")
    rc2, stdout2, stderr2 = run_cmd([QMD_BIN, "embed"])
    reindex_ok = (rc == 0 and rc2 == 0)
    if rc2 != 0:
        print(f"   ⚠️  qmd embed returned {rc2}")
        print(f"   {stderr2[:200]}")
    else:
        print(f"   ✅ qmd embed complete")
    if stdout2.strip():
        print(f"   {stdout2.strip()[:200]}")

    # Step 3: Search tests
    print("\n3. Running search tests...")
    test_results = run_tests()
    all_pass = True
    for query, expected, passed, output in test_results:
        status = "✅" if passed else "❌"
        print(f"   {status} \"{query}\" → expected {expected} → {'PASS' if passed else 'FAIL'}")
        if not passed:
            all_pass = False

    # Step 4: Update health
    health = update_health(test_results, reindex_ok)
    print(f"\n4. Health updated: {health['tests_passed']}/{health['tests_total']} tests passed")
    print(f"   Written to: {HEALTH_FILE}")

    if not all_pass:
        print("\n⚠️  Some tests failed. Exiting with code 1.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")


if __name__ == "__main__":
    main()
