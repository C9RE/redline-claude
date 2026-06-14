#!/usr/bin/env bash
# Redline installer for Claude Code.
#   ./install.sh          copy scripts + print the settings.json to paste
#   ./install.sh --apply  also merge statusLine + hook into ~/.claude/settings.json (backed up first)
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)/scripts"
DEST="$HOME/.claude"
SETTINGS="$DEST/settings.json"

mkdir -p "$DEST"
cp "$SRC/redline-statusline.py" "$SRC/redline-hook.py" "$DEST/"
chmod +x "$DEST/redline-statusline.py" "$DEST/redline-hook.py"
echo "✓ Installed scripts to $DEST/"

read -r -d '' SNIPPET <<'JSON' || true
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude/redline-statusline.py"
  },
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "python3 ~/.claude/redline-hook.py" } ] }
    ]
  }
}
JSON

if [ "${1:-}" = "--apply" ]; then
  command -v python3 >/dev/null || { echo "python3 required for --apply" >&2; exit 1; }
  [ -f "$SETTINGS" ] && cp "$SETTINGS" "$SETTINGS.bak.$(date +%s)" && echo "✓ Backed up settings.json"
  python3 - "$SETTINGS" <<'PY'
import json, os, sys
p = sys.argv[1]
d = json.load(open(p)) if os.path.exists(p) and os.path.getsize(p) else {}
d["statusLine"] = {"type": "command", "command": "python3 ~/.claude/redline-statusline.py"}
hooks = d.setdefault("hooks", {})
ups = hooks.setdefault("UserPromptSubmit", [])
cmd = "python3 ~/.claude/redline-hook.py"
if not any(cmd in json.dumps(e) for e in ups):
    ups.append({"hooks": [{"type": "command", "command": cmd}]})
json.dump(d, open(p, "w"), indent=2)
print("✓ Patched", p)
PY
  echo "Restart Claude Code to activate."
else
  echo
  echo "Add this to $SETTINGS (merge with what's there), then restart Claude Code:"
  echo "$SNIPPET"
  echo
  echo "Or re-run with --apply to patch settings.json automatically."
fi
