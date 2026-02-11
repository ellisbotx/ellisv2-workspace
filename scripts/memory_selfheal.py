#!/usr/bin/env python3
"""Memory Self-Heal — Monitor, repair, and verify memory system health."""

import json
import os
import subprocess
import sys
from datetime import datetime

QMD_BIN = "/Users/ellisbot/.bun/bin/qmd"
WORKSPACE = "/Users/ellisbot/.openclaw/workspace"
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
TOPICS_DIR = os.path.join(MEMORY_DIR, "topics")
HEALTH_FILE = os.path.join(MEMORY_DIR, "health.json")
CRITICAL_FLAG = "/tmp/memory_critical_failure"

TOPIC_FILES = {
    "business.md": "# Business\n\nBrand strategy, financials, SKU data, portfolio decisions.\n",
    "preferences.md": "# Preferences\n\nMarco's rules, communication style, standing instructions.\n",
    "systems.md": "# Systems\n\nTools, access, infrastructure, Discord routing.\n",
    "agents.md": "# Agents\n\nTeam setup, protocols, cross-validation rules.\n",
    "lessons.md": "# Lessons\n\nMistakes, learnings, best practices.\n",
}

SEARCH_TESTS = [
    ("Card Plug margin", ["40%"]),
    ("brevity direct", ["direct", "brevity"]),
    ("Codex Opus", ["Codex", "Opus"]),
    ("ROAS breakeven", ["3.0", "ROAS"]),
    ("FIX IMMEDIATELY memory broken", ["FIX", "fix", "IMMEDIATELY", "immediately"]),
]


def run_cmd(args, cwd=WORKSPACE):
    try:
        result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, timeout=120)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def check_qmd_index():
    """Check if qmd index exists and has >10 files."""
    rc, stdout, stderr = run_cmd([QMD_BIN, "status"])
    # Try to parse file count from output
    combined = stdout + stderr
    # Look for number patterns suggesting indexed files
    import re
    numbers = re.findall(r'(\d+)\s*(?:file|doc|item|entri)', combined.lower())
    if numbers:
        count = int(numbers[0])
        return count > 10, count
    # If status works at all, assume it's ok but unknown count
    return rc == 0, -1


def run_reindex():
    """Run full re-index."""
    print("  Running qmd update...")
    rc1, _, err1 = run_cmd([QMD_BIN, "update"])
    print("  Running qmd embed...")
    rc2, _, err2 = run_cmd([QMD_BIN, "embed"])
    return rc1 == 0 and rc2 == 0


def check_topic_files():
    """Check all topic files exist and have >5 lines. Fix missing ones."""
    issues = []
    for filename, template in TOPIC_FILES.items():
        filepath = os.path.join(TOPICS_DIR, filename)
        if not os.path.exists(filepath):
            os.makedirs(TOPICS_DIR, exist_ok=True)
            with open(filepath, "w") as f:
                f.write(template)
            issues.append(f"Created missing {filename}")
        else:
            with open(filepath, "r") as f:
                lines = f.readlines()
            if len(lines) < 5:
                issues.append(f"{filename} has only {len(lines)} lines (< 5)")
    return issues


def check_daily_log():
    """Ensure today's daily log exists."""
    today = datetime.now().strftime("%Y-%m-%d")
    daily_path = os.path.join(MEMORY_DIR, f"{today}.md")
    if not os.path.exists(daily_path):
        os.makedirs(MEMORY_DIR, exist_ok=True)
        with open(daily_path, "w") as f:
            f.write(f"# Daily Log — {today}\n\n")
        return f"Created daily log for {today}"
    return None


def run_search_tests():
    """Run search verification tests."""
    results = []
    for query, expected_any in SEARCH_TESTS:
        rc, stdout, stderr = run_cmd([QMD_BIN, "search", query, "-n", "10"])
        output = stdout + stderr
        passed = any(exp.lower() in output.lower() for exp in expected_any)
        results.append((query, expected_any, passed))
    return results


def update_health(data):
    os.makedirs(os.path.dirname(HEALTH_FILE), exist_ok=True)
    with open(HEALTH_FILE, "w") as f:
        json.dump(data, f, indent=2)


def main():
    print("🏥 Memory Self-Heal Monitor")
    print("=" * 40)
    
    health = {"timestamp": datetime.now().isoformat(), "checks": {}}
    critical = False
    did_reindex = False

    # 1. Check qmd index
    print("\n1. Checking qmd index...")
    index_ok, count = check_qmd_index()
    if not index_ok:
        print(f"   ⚠️  Index missing or small (count={count}). Re-indexing...")
        reindex_ok = run_reindex()
        did_reindex = True
        print(f"   {'✅' if reindex_ok else '❌'} Re-index {'succeeded' if reindex_ok else 'failed'}")
        health["checks"]["reindex"] = reindex_ok
    else:
        print(f"   ✅ Index OK (count={count})")
        health["checks"]["index"] = True

    # 2. Check topic files
    print("\n2. Checking topic files...")
    issues = check_topic_files()
    if issues:
        for issue in issues:
            print(f"   🔧 {issue}")
    else:
        print("   ✅ All topic files present")
    health["checks"]["topic_files"] = len(issues) == 0
    health["checks"]["topic_issues"] = issues

    # 3. Check daily log
    print("\n3. Checking daily log...")
    daily_result = check_daily_log()
    if daily_result:
        print(f"   🔧 {daily_result}")
    else:
        print("   ✅ Daily log exists")
    health["checks"]["daily_log"] = True

    # 4. Search tests
    print("\n4. Running search tests...")
    test_results = run_search_tests()
    tests_passed = 0
    for query, expected, passed in test_results:
        status = "✅" if passed else "❌"
        print(f"   {status} \"{query}\" → {'PASS' if passed else 'FAIL'}")
        if passed:
            tests_passed += 1

    health["checks"]["search_tests"] = {
        "passed": tests_passed,
        "total": len(test_results),
        "details": [{"query": q, "expected": e, "passed": p} for q, e, p in test_results],
    }

    # 5. If search fails and we already reindexed, that's critical
    all_pass = tests_passed == len(test_results)
    if not all_pass and did_reindex:
        critical = True
        print(f"\n🚨 CRITICAL: Search tests failing after re-index!")
        with open(CRITICAL_FLAG, "w") as f:
            f.write(f"Memory critical failure at {datetime.now().isoformat()}\n")
            f.write(f"Tests passed: {tests_passed}/{len(test_results)}\n")
    elif not all_pass and not did_reindex:
        # Try reindex then retest
        print("\n   Attempting re-index to fix search...")
        reindex_ok = run_reindex()
        did_reindex = True
        if reindex_ok:
            test_results2 = run_search_tests()
            tests_passed2 = sum(1 for _, _, p in test_results2 if p)
            if tests_passed2 > tests_passed:
                print(f"   🔧 Improved: {tests_passed} → {tests_passed2}/{len(test_results2)}")
                test_results = test_results2
                tests_passed = tests_passed2
                all_pass = tests_passed == len(test_results)
            if not all_pass:
                critical = True
                print(f"\n🚨 CRITICAL: Search tests still failing after re-index!")
                with open(CRITICAL_FLAG, "w") as f:
                    f.write(f"Memory critical failure at {datetime.now().isoformat()}\n")

    # Remove critical flag if all good
    if all_pass and os.path.exists(CRITICAL_FLAG):
        os.remove(CRITICAL_FLAG)

    health["all_pass"] = all_pass
    health["critical"] = critical
    update_health(health)

    # Summary
    print(f"\n{'=' * 40}")
    print(f"📊 Summary: {tests_passed}/{len(test_results)} search tests passed")
    print(f"   Topic files: {'✅' if not issues else '🔧 fixed'}")
    print(f"   Status: {'✅ HEALTHY' if all_pass else '🚨 CRITICAL' if critical else '⚠️ DEGRADED'}")
    print(f"   Health file: {HEALTH_FILE}")

    if critical:
        sys.exit(2)
    elif not all_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()
