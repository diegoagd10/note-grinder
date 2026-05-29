# note-grinder

Watches a folder of raw reading notes and automatically distils them into Obsidian-ready study notes optimised for active recall.

## How it works

Two daemons cooperate:

| Daemon | Role |
|---|---|
| **Watcher** | Monitors `RawNotes/` for files whose `process_status` changes to `Ready`, enqueues them in SQLite, and starts the Processor via systemd if it is not already running. |
| **Processor** | Drains the SQLite queue, runs each note through grammar correction then distillation (both via `mmx text chat`), and writes the resulting study notes to `Notes/`. Stops itself after 3 consecutive empty polls (~15 s idle). |

### Note lifecycle

```
Creating → Ready → Grammar Reviewed → Done
```

- **Creating** — set by you while writing; Watcher ignores this status.
- **Ready** — signals the note is finished; Watcher enqueues it.
- **Grammar Reviewed** — grammar correction done; Processor moves on to distillation.
- **Done** — distillation complete; a `## Created Notes` section is appended to the raw file listing the generated notes.

### Directory layout

| Path | Purpose |
|---|---|
| `~/Documents/Diego_Second_Brain/03_Study/RawNotes/` | Watched input directory |
| `~/Documents/Diego_Second_Brain/03_Study/Notes/` | Generated study notes output |
| `~/.local/share/note-grinder/queue.db` | SQLite queue and processor state |

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- [`mmx` CLI](https://github.com/mmxlabs/mmx) — authenticated and available on `$PATH`

## Setup

```bash
git clone git@github.com:diegoagd10/note-grinder.git
cd note-grinder
uv sync
```

## Running the daemons

### Option 1 — manually (development / quick test)

Run each daemon in a separate terminal from the project root:

```bash
# Watcher
uv run python -c "from src.watcher import main; main()"

# Processor (in another terminal)
uv run python -c "from src.processor_main import main; main()"
```

Both daemons handle `SIGTERM` for clean shutdown (`Ctrl+C` works in the terminal).

### Option 2 — systemd user services (recommended)

The Watcher auto-starts the Processor by calling `systemctl --user start note-processor`, so the service name **must** be `note-processor`.

**1. Create the Processor unit** — `~/.config/systemd/user/note-processor.service`

```ini
[Unit]
Description=note-grinder processor daemon
After=default.target

[Service]
Type=simple
WorkingDirectory=%h/Projects/note-grinder
ExecStart=%h/Projects/note-grinder/.venv/bin/python -c "from src.processor_main import main; main()"
Restart=on-failure
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

**2. Create the Watcher unit** — `~/.config/systemd/user/note-watcher.service`

```ini
[Unit]
Description=note-grinder watcher daemon
After=default.target

[Service]
Type=simple
WorkingDirectory=%h/Projects/note-grinder
ExecStart=%h/Projects/note-grinder/.venv/bin/python -c "from src.watcher import main; main()"
Restart=on-failure
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

**3. Enable and start**

```bash
systemctl --user daemon-reload
systemctl --user enable --now note-watcher
```

Only the Watcher needs to be enabled. It starts the Processor on demand whenever a note is enqueued, and the Processor stops itself when idle.

**4. Check status and logs**

```bash
systemctl --user status note-watcher
systemctl --user status note-processor
journalctl --user -u note-watcher -f
journalctl --user -u note-processor -f
```

## Running tests

```bash
uv run pytest
```
