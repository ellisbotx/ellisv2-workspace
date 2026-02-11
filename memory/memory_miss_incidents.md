# Memory Miss Incident Tracker

Tracks every recall failure, fabrication, or missed capture event.

## Fields
- Date/time
- Trigger question
- What failed (capture / search / behavior)
- Root cause
- Immediate fix applied
- Preventive change added
- Verification proof (query/test)

---

## 2026-02-10 — Finance Recall + Wrong Channel Fabrication
- **Failure type:** Capture + behavior
- **Issue:** Could not recall finance numbers; incorrectly claimed conversation happened in #products
- **Root cause:** Conversation not captured into memory files; guessed provenance under pressure
- **Immediate fix:** Rebuilt index, expanded topic files, added twice-daily health checks
- **Preventive changes:** Auto-capture pipeline + unknown-then-verify guardrail + integrity checks
- **Verification:** 5/5 memory search tests pass; selfheal healthy
