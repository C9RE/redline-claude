#!/usr/bin/env python3
"""Redline statusline for Claude Code.

Shows your Pro/Max usage windows (5h + 7d) right in the status line, colour-coded
green -> yellow -> red as you climb toward the limit, with the reset time.

It reads ONLY the `rate_limits` block that Claude Code itself pipes to the status
line on stdin. It does not replay any OAuth token and makes no network calls, so
it's first-party and ToS-clean.

As a side effect it writes the latest figures to a small cache file
(~/.claude/redline-usage.json) so the companion hook can make Claude aware of the
limit and warn you before you run out. See redline-hook.py.
"""
import sys, json, os, datetime

CACHE = os.path.expanduser(os.environ.get("REDLINE_CACHE", "~/.claude/redline-usage.json"))

def g(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return default

def pct_of(w):
    if not isinstance(w, dict):
        return None
    v = g(w, "used_percentage", "utilization", "used_pct", "percent")
    try:
        return round(float(v))
    except (TypeError, ValueError):
        return None

def reset_of(w):
    return g(w, "resets_at", "reset_at", "resetsAt") if isinstance(w, dict) else None

def fmt_reset(v):
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace(".", "", 1).isdigit()):
            ts = float(v)
            if ts > 1e12:
                ts /= 1000.0
            return datetime.datetime.fromtimestamp(ts).strftime("%H:%M")
        return datetime.datetime.fromisoformat(str(v).replace("Z", "+00:00")).astimezone().strftime("%H:%M")
    except Exception:
        return None

def colour(pct):
    if pct is None:
        return "90"
    if pct >= 85:
        return "91"   # red
    if pct >= 60:
        return "93"   # yellow
    return "92"        # green

def seg(label, w):
    pct = pct_of(w)
    if pct is None:
        return None
    s = f"\x1b[{colour(pct)}m{label} {pct}%\x1b[0m"
    r = fmt_reset(reset_of(w))
    if r:
        s += f"\x1b[90m→{r}\x1b[0m"
    return s

def write_cache(rl):
    try:
        five, seven = g(rl, "five_hour", "fiveHour"), g(rl, "seven_day", "sevenDay")
        out = {
            "five_hour": {"pct": pct_of(five), "resets": fmt_reset(reset_of(five))},
            "seven_day": {"pct": pct_of(seven), "resets": fmt_reset(reset_of(seven))},
            "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        }
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        tmp = CACHE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(out, f)
        os.replace(tmp, CACHE)
    except Exception:
        pass  # cache is best-effort; never break the status line

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        print("claude")
        return

    parts = []
    cwd = g(data, "cwd") or g(g(data, "workspace", default={}) or {}, "current_dir") or os.getcwd()
    parts.append(f"\x1b[96m{os.path.basename(cwd.rstrip('/')) or '/'}\x1b[0m")

    model = g(g(data, "model", default={}) or {}, "display_name") or g(data, "model_display_name")
    if model:
        parts.append(f"\x1b[95m{model}\x1b[0m")

    rl = g(data, "rate_limits", "rateLimits", default={}) or {}
    if rl:
        write_cache(rl)
        for s in (seg("5h", g(rl, "five_hour", "fiveHour")), seg("7d", g(rl, "seven_day", "sevenDay"))):
            if s:
                parts.append(s)

    print(" \x1b[90m·\x1b[0m ".join(parts))

if __name__ == "__main__":
    main()
