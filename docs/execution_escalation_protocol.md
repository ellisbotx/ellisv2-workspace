# Execution Escalation Protocol (Mandatory)

## Purpose
Prevent long stalls, missed updates, and single-model dead ends. When active work is not shipping, escalate fast.

## Applies To
Any task expected to exceed 10 minutes, any multi-step technical implementation, and any task with user frustration or deadline pressure.

## Timebox + Escalation Ladder

### T+0 (start)
- Classify task: Simple / Medium / Complex.
- Set explicit target and first proof checkpoint.

### T+10 minutes (no meaningful progress)
- Spawn first specialist sub-agent.
- Main agent remains front-desk and gives factual update.

### T+20 minutes (still unresolved)
- Spawn second model in parallel for independent attempt.
- Prefer different model family from first attempt.

### T+30 minutes (still unresolved)
- Stop solo implementation attempts.
- Switch to orchestrator-only mode.
- Send blocker summary + fallback options + hard ETA.

## Update Cadence (Proof-Only)
Every 5 minutes, send one of these only:
1. **Done + proof** (what passed)
2. **Blocked + fallback + ETA**

No fluff updates, no optimistic placeholders.

## Failure Kill Switch
- Missing one promised update interval triggers immediate escalation to parallel sub-agent workflow.
- No repeated missed interval on same task.

## Verification Gate
Before claiming complete:
- Show executable proof (command output, message IDs, artifact path, or pass/fail evidence).
- If result impacts numbers/logic, require cross-check by second model or deterministic script.

## Post-Incident Requirement
For any overrun (>30 minutes) or missed cadence:
- Log root cause
- Log missed trigger
- Log preventive patch
- Update lessons/memory

## Success Standard
- Fast escalation, no hidden stalls.
- User sees facts, not guesses.
- Long delays become rare and immediately visible.
