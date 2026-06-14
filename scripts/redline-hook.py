#!/usr/bin/env python3
"""Redline UserPromptSubmit hook for Claude Code.

Makes Claude aware of how much of your Pro/Max session you have left, so it can
warn you ("we may run out before this finishes") and ease off or hand work to a
delegate, instead of you finding out by hitting a wall mid-task.

How it works: the Redline status line writes the latest usage figures (which the
harness gives it first-party) to ~/.claude/redline-usage.json. This hook reads
that cache and, when usage crosses a threshold, injects a short note into Claude's
context for the turn. No OAuth token replay, no network calls.

Thresholds (env-overridable):
  REDLINE_WARN    inject a heads-up at/above this %   (default 75)
  REDLINE_URGENT  stronger wording at/above this %    (default 90)
  REDLINE_STALE   ignore cache older than N seconds    (default 1800)
"""
import sys, json, os, datetime

CACHE = os.path.expanduser(os.environ.get("REDLINE_CACHE", "~/.claude/redline-usage.json"))
WARN = float(os.environ.get("REDLINE_WARN", "75"))
URGENT = float(os.environ.get("REDLINE_URGENT", "90"))
STALE = float(os.environ.get("REDLINE_STALE", "1800"))

def emit(context):
    # UserPromptSubmit: additionalContext is injected into the model's context.
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }))

def main():
    # Drain stdin (hook payload) so Claude Code doesn't see a broken pipe.
    try:
        sys.stdin.read()
    except Exception:
        pass

    try:
        with open(CACHE) as f:
            c = json.load(f)
    except Exception:
        sys.exit(0)  # no cache yet -> stay silent

    # freshness guard
    try:
        age = (datetime.datetime.now() - datetime.datetime.fromisoformat(c["updated_at"])).total_seconds()
        if age > STALE:
            sys.exit(0)
    except Exception:
        pass

    windows = []
    for key, label in (("five_hour", "5-hour"), ("seven_day", "7-day")):
        w = c.get(key) or {}
        pct = w.get("pct")
        if isinstance(pct, (int, float)) and pct >= WARN:
            r = w.get("resets") or w.get("resets_at")
            r = f", resets {r}" if r else ""
            windows.append(f"{label} window at {int(pct)}%{r}")

    if not windows:
        sys.exit(0)

    peak = max((c.get(k, {}) or {}).get("pct") or 0 for k in ("five_hour", "seven_day"))
    tone = ("URGENT: Claude Code session is nearly exhausted"
            if peak >= URGENT else
            "Heads-up: Claude Code session usage is getting high")
    emit(
        f"[Redline] {tone} — {'; '.join(windows)}. "
        "Tell the user plainly that you may run out before the task finishes, and "
        "offer to wrap up, checkpoint progress, or hand offloadable work to a delegate. "
        "Do not silently push on as if usage were unlimited."
    )
    sys.exit(0)

if __name__ == "__main__":
    main()
