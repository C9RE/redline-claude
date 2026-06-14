# 🏁 Redline Claude

**Know when you're about to run out of Claude Code, well before you hit the wall.**

Redline Claude is a tiny, dependency-free status line and hook for [Claude Code](https://www.claude.com/product/claude-code) on a **Pro/Max** plan. It puts your usage windows right in the status line, colour-coded like a tacho climbing toward the limiter, and it lets **Claude itself** see how much session you have left so it can warn you and ease off instead of stalling mid-task.

```
core · Opus 4.8 · 5h 42%→19:00 · 7d 71%→10:00
        green ───────┘            └─── yellow, climbing
```

When you're redlining, the colour goes red and Claude gets a quiet nudge in its context:

> ⚠️ **URGENT: Claude Code session is nearly exhausted.** 5-hour window at 92%, resets 19:00. Tell the user plainly that you may run out before the task finishes, and offer to wrap up, checkpoint, or hand offloadable work to a delegate.

So instead of discovering your limit by getting cut off, Claude says *"heads-up, we might not finish this. Want me to checkpoint?"*

---

## Why it exists

Claude Code shows your limit only if you run `/usage`. It never warns you, and the model itself has **no idea** how much of your window is left, so it happily starts a 20-minute job with 3 minutes of quota. Redline Claude fixes both ends:

- **You** get an always-on meter in the status line.
- **Claude** gets a heads-up injected into its context when you're running hot, so it can act on it.

> Fun fact: this was built in a session that hit its own limit halfway through writing it. The wall is real. Now it has a warning light.

---

## How it works (and why it's safe)

The Claude Code harness pipes a `rate_limits` block to the **status line** on stdin, first-party, no auth gymnastics. Redline Claude:

1. **`redline-statusline.py`** renders the meter and writes the latest figures to `~/.claude/redline-usage.json`.
2. **`redline-hook.py`** (a `UserPromptSubmit` hook) reads that cache and, above a threshold, injects a short note into Claude's context for the turn.

That cache file is the bridge. The status line is the only thing guaranteed to receive `rate_limits`, so it feeds the hook.

It makes **no network calls and replays no tokens**, and it never reads your credentials. It only touches data Claude Code already hands it. That matters: since 2026-01-09 Anthropic bans using Pro/Max subscription tokens in third-party tools, so anything that calls the usage API with your token risks your account. Redline Claude deliberately does not, and never will.

---

## Install

Requires Python 3 (standard library only) and a Claude Code **Pro or Max** plan. The `rate_limits` data only exists on subscription plans, and only populates after the first response in a session.

### Quick

```bash
git clone https://github.com/C9RE/redline-claude.git
cd redline-claude
./install.sh            # copies scripts to ~/.claude/ and prints the config to paste
./install.sh --apply    # ...or also patches ~/.claude/settings.json for you (backs it up first)
```

### Manual

1. Copy the two scripts somewhere stable:
   ```bash
   cp scripts/redline-statusline.py scripts/redline-hook.py ~/.claude/
   chmod +x ~/.claude/redline-*.py
   ```
2. Add to `~/.claude/settings.json` (merge with what's already there):
   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "python3 ~/.claude/redline-statusline.py"
     },
     "hooks": {
       "UserPromptSubmit": [
         {
           "hooks": [
             { "type": "command", "command": "python3 ~/.claude/redline-hook.py" }
           ]
         }
       ]
     }
   }
   ```
3. Restart Claude Code. The status line lights up after the first response.

Want just the meter and not the Claude warnings? Skip the `hooks` block. Want only the warnings and not the meter? You still need the status line installed, since it produces the data the hook reads.

---

## Configure

Thresholds are environment variables. Set them in the hook command, for example `REDLINE_WARN=80 python3 ~/.claude/redline-hook.py`:

| Var | Default | Meaning |
|-----|---------|---------|
| `REDLINE_WARN` | `75` | Inject a heads-up at/above this % |
| `REDLINE_URGENT` | `90` | Stronger wording at/above this % |
| `REDLINE_STALE` | `1800` | Ignore cached figures older than N seconds |
| `REDLINE_CACHE` | `~/.claude/redline-usage.json` | Cache file path (both scripts must agree) |

Status line colour bands: green below 60%, yellow 60 to 84%, red 85% and up.

---

## Limitations (honest)

- **Pro/Max only.** No subscription means no `rate_limits`, so the meter shows just dir and model, and the hook stays silent.
- **Populates after the first response** in a session, not instantly on launch.
- The hook's context injection relies on Claude Code's documented `UserPromptSubmit` to `additionalContext` behaviour. If a future version changes that, the meter still works and only the in-context warning would need a tweak.
- It reports the windows Claude Code exposes (5-hour, 7-day). It is not an exact token counter or a billing tool.

---

## License

MIT © C9RE. Use it, fork it, redline it.
