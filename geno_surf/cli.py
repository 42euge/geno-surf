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
        print("  surf groups                 List native tab groups")
        print("  surf group <name.path> <url…>  Open URLs into a native tab group")
        print("  surf reg [show|pull|push]   Sync groups \u2194 the shared object-notation registry")
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
        p.add_argument("--group", default=None, help="object-notation tab group")
        p.add_argument("--color", default="blue")
        a = p.parse_args(rest)
        r = cdp.open_in_group(a.url, a.group, a.color)
        if a.group:
            print(f"opened into group {_BOLD}{a.group}{_RESET}  {a.url}")
        else:
            print(f"opened {r.get('id','?')[:8]}  {a.url}")

    elif cmd == "groups":
        gs = cdp.list_groups()
        if not gs:
            print(f"{_DIM}no tab groups{_RESET}")
        for g in gs:
            print(f"  {_BOLD}{g.get('title','(untitled)')}{_RESET}  "
                  f"{_DIM}{g.get('color','')}  id={g.get('id')}{_RESET}")

    elif cmd == "focus":
        if not rest:
            raise SystemExit("Usage: surf focus <node|tabId>")
        arg = rest[0]
        res = cdp.focus_group(arg)  # try as an object-notation group first
        if res != "no-group":
            print(f"focused group {_BOLD}{arg}{_RESET} ({res})")
        elif "." in arg:  # looks like a node path, not a tab id
            print(f"{_DIM}no Chrome group '{arg}'{_RESET}")
        else:
            try:
                cdp.activate_tab(arg)
                print(f"focused tab {arg[:8]}")
            except Exception:
                print(f"{_DIM}no tab or group '{arg}'{_RESET}")

    elif cmd == "close":
        if not rest:
            raise SystemExit("Usage: surf close <id>")
        cdp.close_tab(rest[0])
        print(f"closed {rest[0][:8]}")

    elif cmd == "group":
        p = argparse.ArgumentParser(prog="surf group", add_help=False)
        p.add_argument("title", help="object-notation group, e.g. ngrt.main.tickets")
        p.add_argument("urls", nargs="*", help="URLs to open into the group")
        p.add_argument("--color", default="blue")
        a = p.parse_args(rest)
        if not a.urls:
            raise SystemExit("Usage: surf group <title> <url> [url…] [--color C]")
        for u in a.urls:
            cdp.open_in_group(u, a.title, a.color)
        print(f"grouped {len(a.urls)} tab(s) under {_BOLD}{a.title}{_RESET} ({a.color}).")

    elif cmd == "reg":
        from . import registry
        sub = rest[0] if rest else "show"

        if sub == "pull":
            reg = registry.load()
            n = 0
            for g in cdp.groups_with_tabs():
                if not g.get("title"):
                    continue
                registry.node(reg, g["title"])["chrome"] = {
                    "group": g["title"], "color": g.get("color", "blue"),
                    "urls": g.get("urls", [])}
                n += 1
            registry.save(reg)
            print(f"pulled {n} Chrome group(s) → {registry.PATH}")

        elif sub == "push":
            reg = registry.load()
            n = 0
            for path, node in sorted(reg.get("nodes", {}).items()):
                ch = node.get("chrome")
                if ch and ch.get("urls"):
                    for u in ch["urls"]:
                        cdp.open_in_group(u, ch.get("group", path), ch.get("color", "blue"))
                    n += 1
            print(f"pushed {n} node(s) → Chrome tab groups")

        else:  # show
            reg = registry.load()
            nodes = reg.get("nodes", {})
            if not nodes:
                print(f"{_DIM}registry empty ({registry.PATH}){_RESET}")
            for path, node in sorted(nodes.items()):
                surf = []
                if "chrome" in node:
                    surf.append(f"chrome:{len(node['chrome'].get('urls', []))}t/{node['chrome'].get('color','')}")
                if "iterm" in node:
                    surf.append(f"iterm:{node['iterm'].get('tty','?')}")
                print(f"  {_BOLD}{path}{_RESET}  {_DIM}[{' · '.join(surf) or 'no surfaces'}]{_RESET}")

    else:
        raise SystemExit(f"Unknown command '{cmd}'. Try: surf --help")
    return 0


if __name__ == "__main__":
    sys.exit(main())
