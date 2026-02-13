# Self-Reflection Protocol

## Purpose
Catch mistakes early, prevent repeats, and continuously improve memory reliability.

## Daily Mini-Review (10-15 min)
Frequency: Daily at 8:15 PM CST

Checklist:
1. Review latest `memory/health.json` and `memory/slo_status.json`
2. Confirm search tests pass and capture missing count is 0
3. Scan today’s major decisions in `memory/YYYY-MM-DD.md`
4. Log any misses to `memory/memory_miss_incidents.md`
5. Add one small improvement action for tomorrow if needed

Output:
- Post short status in `#system`:
  - What passed
  - What failed
  - What got fixed
  - Improvement planned

## Weekly Deep Review (30-45 min)
Frequency: Sundays at 7:30 PM CST

Checklist:
1. Review all integrity reports from last 7 days (`data/integrity_reports/`)
2. Count incidents and repeated root causes
3. Identify top 3 failure patterns
4. Propose 1-3 concrete system changes
5. Apply low-risk changes immediately
6. Log outcomes in `memory/topics/lessons.md`

Output:
- Post full review in `#system` with:
  - Incident trend
  - Root causes
  - Changes made
  - Next-week focus

## Non-Negotiables
- No fabrication: unknown first, verify second
- Fix first, report second
- Every repeat failure must produce a new guardrail
