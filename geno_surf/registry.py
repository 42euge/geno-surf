"""The shared object-notation registry — the source of truth that unifies
geno-tt (iTerm) and geno-surf (Chromium).

One JSON file at ~/.geno/registry.json (stdlib, dependency-free). Each node is
keyed by its object path (`ngrt.main.tickets`) and carries per-surface
attachments; every tool `pull`s its surface's state in and `push`es it back out:

    {
      "nodes": {
        "ngrt.main.tickets": {
          "chrome": {"group": "ngrt.main.tickets", "color": "blue",
                     "urls": ["https://…"]},
          "iterm":  {"tty": "ttys016"}
        }
      }
    }

The schema is the contract; geno-tt writes the `iterm` key, geno-surf the
`chrome` key. Neither clobbers the other's surface.
"""

import json
from pathlib import Path

# Dedicated file — NOT ~/.geno/registry.json (that's geno-tools' repo-discovery
# registry). This is the cross-surface workspace object-notation tree.
PATH = Path.home() / ".geno" / "workspace.json"


def load() -> dict:
    if PATH.exists():
        try:
            data = json.loads(PATH.read_text())
            data.setdefault("nodes", {})
            return data
        except (ValueError, OSError):
            pass
    return {"nodes": {}}


def save(reg: dict) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(reg, indent=2, sort_keys=True) + "\n")


def node(reg: dict, path: str) -> dict:
    return reg.setdefault("nodes", {}).setdefault(path, {})
