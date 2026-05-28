# Study Note Watcher — Shared Knowledge

**Architecture**
- Watcher daemon: uses watchdog `on_modified` to detect files with `process_status: Ready`, inserts into SQLite queue, auto-starts processor when queue becomes non-empty
- Processor daemon: polls SQLite every 5s, takes up to 5 `queued` items, runs grammar + distilling pipeline, picks up `processing` items on restart
- Processor stops after 3 consecutive empty polls (15s); watcher restarts it

**Directory structure**
- Watch dir: `~/Documents/Diego_Second_Brain/03_Study/RawNotes/`
- Output dir: `~/Documents/Diego_Second_Brain/03_Study/Notes/`

**SQLite schema**
- `queue_items`: id, filename, status (queued/processing/done/failed), created_at, updated_at
- `processor_state`: key, value (status, pid, last_seen)

**State machine (frontmatter `process_status` field)**
`Creating` → `Ready` → `Grammar Reviewed` → `Done`

- `Creating` — user writing, watcher ignores
- `Ready` — watcher inserts into queue once
- `Grammar Reviewed` — grammar step done by processor
- `Done` — distilling complete

**Deduplication**: if already in queue or frontmatter is not `Ready`, no re-insert

**Processing pipeline per item**
1. Verify frontmatter is `Ready` (race condition check)
2. Set queue status to `processing`
3. Grammar: `mmx text chat` — fixes typos only, preserves Spanish prose, no restructure → update frontmatter to `Grammar Reviewed`
4. Distill: `mmx text chat` — converts to Arg/Why/Example/Question, creates granular obsidian notes with Spanish question filenames + emojis → update frontmatter to `Done`, append `## Created Notes` to raw file body

**Concurrency**
- Max 5 parallel `mmx` workers per processor batch
- Processor blocked while workers run, then polls queue again

**Retry**: 3 attempts per step on failure → leave at current frontmatter status

**Raw file after processing**: left in `RawNotes/` with `Done` status, body has `## Created Notes` list

**Logging**: `[timestamp] Step: old_status → new_status | filename` + errors to stdout

**PID file**: `~/.run/study-note-watcher.pid` for stop script

**Authentication**: assumes `mmx-cli` already authenticated

**User workflow**
1. Create raw note on phone, frontmatter with `process_status: Creating`
2. Write raw notes while reading
3. Finish chapter → change status to `Ready`
4. Watcher detects transition → inserts into queue
5. Processor picks up → grammar → distil → granular notes in `03_Study/Notes/`

**Error recovery**: on restart, processor picks up both `queued` and `processing` items