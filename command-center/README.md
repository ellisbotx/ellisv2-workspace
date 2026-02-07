# Marco's Command Center (Next.js + Convex)

Ops dashboard with 3 core views:
- **Activity Feed** (log every action; infinite scroll + filters)
- **Calendar** (weekly scheduled task view)
- **Global Search** (documents + memory + activity + tasks)

## Tech
- Next.js (App Router)
- Convex (DB + backend)
- Tailwind (dark mode)

## Local Setup

### 1) Install
```bash
cd /Users/ellisbot/.openclaw/workspace/command-center
npm install
```

### 2) Start Convex (local)
```bash
npm run convex:dev
```
This writes `.env.local` with `NEXT_PUBLIC_CONVEX_URL`.

### 3) Seed + index workspace docs
In a second terminal:
```bash
npm run seed
npm run index
```
Indexing scans `/Users/ellisbot/.openclaw/workspace` by default.
Override:
```bash
WORKSPACE_ROOT=/path/to/root npm run index
```

### 4) Start Next.js
```bash
npm run dev
```
Open http://localhost:3000

## Logging Activities (for Ellis/agents)

### Option A: from the UI
Activity page has a **+ Test log** button.

### Option B: call the Convex mutation
Mutation: `api.activities.log`

Payload:
- `agent` (string)
- `actionType` (string)
- `description` (string)
- `outcome`: `success | failed | partial`
- optional: `related` (array of file paths/links), `metadata`

## Deployment (Vercel + Convex Cloud)

1. **Convex:**
   - `npx convex login`
   - `npx convex deploy`
2. **Vercel:**
   - Import this repo
   - Add env var: `NEXT_PUBLIC_CONVEX_URL` from your Convex deployment
   - Deploy

## Notes / Next improvements
- Materialize recurring task *occurrences* (instead of only `nextRunAt`)
- Import OpenClaw cron jobs automatically (needs gateway API wiring)
- File watcher to auto-reindex on changes (can be done with `chokidar` in a local daemon)
