#!/usr/bin/env python3
"""surf — Chromium orchestration for the geno agent (browser half of geno-tt).

Drives a dedicated Chromium over the DevTools Protocol, addressed by the same
object-notation registry as geno-tt (`ngrt.main.tickets`, `hil.plans`, ...).
Safari stays human; this is the agent's browser.
"""

import argparse
import sys

from . import chrome_cdp as cdp

_BOLD, _DIM, _RESET = "\033[1m", "\033[2m", "\033[0m"


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("surf — Chromium orchestration (geno-surf)")
        print("  surf launch                 Start the agent's Chromium (remote debugging)")
        print("  surf ls                     List open tabs (id · title · url)")
        print("  surf open <url> [--group G] Open a tab (group = object path; see note)")
        print("  surf close <id>             Close a tab")
        print("  surf focus <id>             Activate a tab")
        print("  surf group <name.path> …    Group tabs (native groups need the extension)")
        print(f"{_DIM}  Object notation mirrors geno-tt: program.area.aspect.{_RESET}")
        return 0

    cmd, rest = argv[0], argv[1:]

    if cmd == "launch":
        print(cdp.launch())
        return 0

    if not cdp.is_up():
        raise SystemExit("Chromium isn't running with remote debugging. Run: surf launch")

    if cmd == "ls":
        for t in cdp.list_tabs():
            tid = t.get("id", "")[:8]
            title = (t.get("title") or "")[:44]
            print(f"  {tid}  {_BOLD}{title}{_RESET}  {_DIM}{t.get('url','')[:60]}{_RESET}")

    elif cmd == "open":
        p = argparse.ArgumentParser(prog="surf open", add_help=False)
        p.add_argument("url")
        p.add_argument("--group", default=None)
        a = p.parse_args(rest)
        t = cdp.new_tab(a.url)
        print(f"opened {t.get('id','?')[:8]}  {a.url}")
        if a.group:
            print(f"{_DIM}note: native tab-group '{a.group}' assignment needs the "
                  f"geno-surf extension (phase 2); tab opened ungrouped.{_RESET}")

    elif cmd == "focus":
        if not rest:
            raise SystemExit("Usage: surf focus <id>")
        cdp.activate_tab(rest[0])
        print(f"focused {rest[0][:8]}")

    elif cmd == "close":
        if not rest:
            raise SystemExit("Usage: surf close <id>")
        cdp.close_tab(rest[0])
        print(f"closed {rest[0][:8]}")

    elif cmd == "group":
        raise SystemExit(
            "Native Chrome tab groups aren't in the DevTools Protocol — they're "
            "the chrome.tabGroups extension API. `surf group` lands in phase 2 with "
            "the bundled extension + native-messaging bridge. Until then, model a "
            "node as its own window/tabs via `surf open`.")

    else:
        raise SystemExit(f"Unknown command '{cmd}'. Try: surf --help")
    return 0


if __name__ == "__main__":
    sys.exit(main())
