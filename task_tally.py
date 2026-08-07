#!/usr/bin/env python3
"""Task_Tally — CLI time tracker.
Start and stop tasks, tag projects, export CSV reports. Zero deps."""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta


RUNNING_FILE = os.path.expanduser("~/.task_tally_running.json")
LOG_FILE = os.path.expanduser("~/.task_tally_log.jsonl")


def now_iso():
    return datetime.now().isoformat()


def now_ts():
    return time.time()


def get_running():
    """Get currently running task, or None."""
    if os.path.exists(RUNNING_FILE):
        try:
            with open(RUNNING_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def save_running(task):
    with open(RUNNING_FILE, "w") as f:
        json.dump(task, f, indent=2)


def clear_running():
    if os.path.exists(RUNNING_FILE):
        os.remove(RUNNING_FILE)


def append_log(entry):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def read_log():
    """Read all log entries."""
    entries = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return entries


def format_duration(seconds):
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}m {s}s"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"


def parse_date_range(args):
    """Parse date range from args. Returns (start_date, end_date) or (None, None) for all."""
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    is_range = False
    start = None
    end = None

    if hasattr(args, 'today') and args.today:
        start = today
        end = today + timedelta(days=1)
        is_range = True
    elif hasattr(args, 'yesterday') and args.yesterday:
        start = today - timedelta(days=1)
        end = today
        is_range = True
    elif hasattr(args, 'week') and args.week:
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=7)
        is_range = True
    elif hasattr(args, 'month') and args.month:
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1)
        else:
            end = today.replace(month=today.month + 1, day=1)
        is_range = True
    elif hasattr(args, 'all') and args.all:
        start = None
        end = None
        is_range = True

    return start, end, is_range


def filter_log(entries, start=None, end=None, project=None, date_range_applied=False):
    """Filter log entries by date range and project."""
    filtered = entries[:]

    if date_range_applied and start is not None:
        start_ts = start.timestamp()
        filtered = [e for e in filtered if e.get("start") and e["start"] >= start_ts]
    if date_range_applied and end is not None:
        end_ts = end.timestamp()
        filtered = [e for e in filtered if e.get("start") and e["start"] < end_ts]

    if project:
        filtered = [e for e in filtered if e.get("project", "").lower() == project.lower()]

    return filtered


def cmd_start(args):
    running = get_running()
    if running:
        elapsed = now_ts() - running["start"]
        print(f"Already tracking: '{running['task']}' ({format_duration(elapsed)})", file=sys.stderr)
        print("Stop it first with 'task_tally stop'", file=sys.stderr)
        sys.exit(1)

    task = {
        "task": args.task,
        "project": args.project or "",
        "tag": args.tag or "",
        "start": now_ts(),
        "start_iso": now_iso(),
    }
    save_running(task)

    if args.format == "json":
        print(json.dumps(task, indent=2))
    else:
        proj_str = f" [{args.project}]" if args.project else ""
        tag_str = f" #{args.tag}" if args.tag else ""
        print(f"▶ Started: {args.task}{proj_str}{tag_str}")
        print(f"  Started at: {task['start_iso']}")


def cmd_stop(args):
    running = get_running()
    if not running:
        print("No task currently running.", file=sys.stderr)
        sys.exit(1)

    end_time = now_ts()
    duration = end_time - running["start"]

    entry = {
        "task": running["task"],
        "project": running.get("project", ""),
        "tag": running.get("tag", ""),
        "start": running["start"],
        "end": end_time,
        "duration_seconds": round(duration, 1),
        "note": args.note or "",
    }
    append_log(entry)
    clear_running()

    if args.format == "json":
        print(json.dumps(entry, indent=2))
    else:
        print(f"■ Stopped: {entry['task']} — {format_duration(duration)}")
        if args.note:
            print(f"  Note: {args.note}")


def cmd_status(args):
    running = get_running()

    if args.format == "json":
        if running:
            elapsed = now_ts() - running["start"]
            running["elapsed_seconds"] = round(elapsed, 1)
            running["elapsed_human"] = format_duration(elapsed)
        print(json.dumps(running, indent=2))
    else:
        if not running:
            print("No task currently running.")
        else:
            elapsed = now_ts() - running["start"]
            proj_str = f" [{running.get('project', '')}]" if running.get("project") else ""
            tag_str = f" #{running.get('tag', '')}" if running.get("tag") else ""
            print(f"▶ Running: {running['task']}{proj_str}{tag_str}")
            print(f"  Elapsed: {format_duration(elapsed)}")
            print(f"  Started: {running['start_iso']}")


def cmd_log(args):
    entries = read_log()
    start, end, date_filtered = parse_date_range(args)
    project = args.project if hasattr(args, 'project') else None
    filtered = filter_log(entries, start, end, project, date_filtered)

    if args.format == "json":
        print(json.dumps(filtered, indent=2))
    else:
        if not filtered:
            print("No entries found.")
            return

        total_duration = sum(e.get("duration_seconds", 0) for e in filtered)
        print(f"\nTime Log ({len(filtered)} entries, {format_duration(total_duration)} total):")
        print("-" * 90)
        for e in filtered:
            task = e.get("task", "?")
            proj = e.get("project", "")
            tag = e.get("tag", "")
            dur = format_duration(e.get("duration_seconds", 0))
            start_iso = e.get("start_iso", "")
            if not start_iso and e.get("start"):
                start_iso = datetime.fromtimestamp(e["start"]).isoformat()

            proj_tag = ""
            if proj:
                proj_tag += f" [{proj}]"
            if tag:
                proj_tag += f" #{tag}"
            print(f"  {start_iso[:19]:19s}  {task:20s}{proj_tag:25s}  {dur:>8s}")

            note = e.get("note", "")
            if note:
                print(f"  {'':19s}  ↳ {note}")

        print("-" * 90)
        print(f"  Total: {format_duration(total_duration)}")


def cmd_report(args):
    entries = read_log()
    start, end, date_filtered = parse_date_range(args)
    project = args.project if hasattr(args, 'project') else None
    filtered = filter_log(entries, start, end, project, date_filtered)

    if not filtered:
        if args.format == "json":
            print(json.dumps({"summary": [], "total_hours": 0}))
        else:
            print("No entries found for the selected period.")
        return

    # Aggregate by project and task
    project_tasks = {}
    for e in filtered:
        proj = e.get("project", "") or "(no project)"
        task = e.get("task", "?")
        dur = e.get("duration_seconds", 0)

        if proj not in project_tasks:
            project_tasks[proj] = {}
        if task not in project_tasks[proj]:
            project_tasks[proj][task] = 0
        project_tasks[proj][task] += dur

    total_seconds = sum(sum(tasks.values()) for tasks in project_tasks.values())
    total_hours = total_seconds / 3600

    if args.format == "json":
        result = {
            "summary": [],
            "total_seconds": round(total_seconds, 1),
            "total_hours": round(total_hours, 2),
        }
        for proj, tasks in project_tasks.items():
            proj_entry = {"project": proj, "tasks": [], "total_seconds": 0, "total_hours": 0}
            for task, dur in tasks.items():
                proj_entry["tasks"].append({
                    "task": task,
                    "duration_seconds": round(dur, 1),
                    "duration_hours": round(dur / 3600, 2),
                })
                proj_entry["total_seconds"] += dur
            proj_entry["total_hours"] = round(proj_entry["total_seconds"] / 3600, 2)
            result["summary"].append(proj_entry)
        print(json.dumps(result, indent=2))
        return

    # ASCII bar chart
    max_bar_width = 40
    max_dur = max(
        max(tasks.values()) for tasks in project_tasks.values()
    ) if project_tasks else 1

    print(f"\nTime Report — Total: {format_duration(total_seconds)} ({total_hours:.1f}h)")
    print("=" * 70)

    for proj, tasks in sorted(project_tasks.items()):
        proj_total = sum(tasks.values())
        proj_hours = proj_total / 3600
        print(f"\n📁 {proj} — {format_duration(proj_total)} ({proj_hours:.1f}h)")
        print("-" * 50)
        for task, dur in sorted(tasks.items(), key=lambda x: x[1], reverse=True):
            bar_len = int((dur / max_dur) * max_bar_width) if max_dur > 0 else 0
            bar = "█" * bar_len
            print(f"  {task:25s}  {bar} {format_duration(dur)}")


def main():
    parser = argparse.ArgumentParser(
        description="Task_Tally — CLI time tracker. Zero deps.",
        prog="task_tally",
    )
    sub = parser.add_subparsers(dest="command", help="Subcommand")

    # start
    p_start = sub.add_parser("start", help="Start tracking a task")
    p_start.add_argument("task", help="Task name")
    p_start.add_argument("--project", help="Project name")
    p_start.add_argument("--tag", help="Tag for the task")
    p_start.add_argument("--format", choices=["text", "json"], default="text")

    # stop
    p_stop = sub.add_parser("stop", help="Stop current task")
    p_stop.add_argument("--note", help="Note to attach")
    p_stop.add_argument("--format", choices=["text", "json"], default="text")

    # status
    p_status = sub.add_parser("status", help="Show currently running task")
    p_status.add_argument("--format", choices=["text", "json"], default="text")

    # log
    p_log = sub.add_parser("log", help="Show time log")
    p_log.add_argument("--project", help="Filter by project name")
    p_log.add_argument("--today", action="store_true", help="Show today's entries")
    p_log.add_argument("--yesterday", action="store_true", help="Show yesterday's entries")
    p_log.add_argument("--week", action="store_true", help="Show this week's entries")
    p_log.add_argument("--all", action="store_true", help="Show all entries")
    p_log.add_argument("--format", choices=["text", "json"], default="text")

    # report
    p_report = sub.add_parser("report", help="Summarize hours by project and task")
    p_report.add_argument("--project", help="Filter by project name")
    p_report.add_argument("--week", action="store_true", help="Show this week's summary")
    p_report.add_argument("--month", action="store_true", help="Show this month's summary")
    p_report.add_argument("--all", action="store_true", help="Show all-time summary")
    p_report.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "start":
        cmd_start(args)
    elif args.command == "stop":
        cmd_stop(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "log":
        cmd_log(args)
    elif args.command == "report":
        cmd_report(args)


if __name__ == "__main__":
    main()
