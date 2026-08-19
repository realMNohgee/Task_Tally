# Task_Tally
![CI](https://github.com/realMNohgee/Task_Tally/actions/workflows/ci.yml/badge.svg) ![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg) ![License](https://img.shields.io/badge/license-MIT-blue.svg)

CLI time tracker. Start and stop tasks, tag projects, export CSV reports. **Zero dependencies** — Python stdlib only.

## Installation

```bash
curl -O https://raw.githubusercontent.com/realMNohgee/Task_Tally/main/task_tally.py
chmod +x task_tally.py
```

Or clone:

```bash
git clone git@github.com:realMNohgee/Task_Tally.git
```

## Usage

```bash
# Start tracking a task
python3 task_tally.py start "Code Review" --project Hermtica --tag backend

# Check current status
python3 task_tally.py status

# Stop the current task
python3 task_tally.py stop --note "Reviewed PR #42"

# View time log
python3 task_tally.py log --today
python3 task_tally.py log --project Hermtica --week

# Generate reports
python3 task_tally.py report --week
python3 task_tally.py report --month --format json
```

## Subcommands

| Subcommand | Description | Example |
|-----------|-------------|---------|
| `start` | Start tracking a task | `task_tally start "Bug Fix" --project App --tag ui` |
| `stop` | Stop current task | `task_tally stop --note "Fixed navbar"` |
| `status` | Show currently running task and elapsed time | `task_tally status` |
| `log` | Show time log with filters | `task_tally log --week --project App` |
| `report` | Summarize hours by project and task (ASCII chart) | `task_tally report --month` |

## Options

All subcommands support `--format json` for machine-readable output.

| Flag | Subcommands | Description |
|------|-------------|-------------|
| `--project NAME` | start, log, report | Project name |
| `--tag TAG` | start | Tag for the task |
| `--note TEXT` | stop | Note to attach to stopped task |
| `--today` | log | Show today's entries |
| `--yesterday` | log | Show yesterday's entries |
| `--week` | log, report | This week |
| `--month` | report | This month |
| `--all` | log, report | All entries (all-time) |

## Data Storage

- Running task: `~/.task_tally_running.json`
- Time log: `~/.task_tally_log.jsonl`

Each log entry (JSONL format):
```json
{"task": "...", "project": "...", "tag": "...", "start": 1234567890.0, "end": 1234567890.0, "duration_seconds": 3600.0, "note": "..."}
```

## Multi-Domain Use

| Domain | Usage |
|--------|-------|
| Freelancing | Track billable hours per client/project |
| Development | Log time spent on features, bugs, code review |
| Project Management | Generate weekly reports for stakeholders |
| Personal | Track habits, study sessions, workouts |
| Legal | Time tracking for compliance/audit trails |
| Consulting | Export CSV reports for invoicing |

Built for the [Hermtica Marketplace](https://hermtica.com).
