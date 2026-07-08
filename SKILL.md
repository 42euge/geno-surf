---
name: geno-surf
description: >-
  Chromium orchestration for the geno agent (the `surf` CLI). Use to launch and
  drive the agent's Chromium — list/open/focus/close tabs — addressed by the
  shared object-notation registry. Safari is human; this is the agent's browser.
allowed-tools: "Bash(surf *)"
metadata:
  author: 42euge
  version: "0.4.0"
---

# geno-surf — Chromium orchestration

The `surf` CLI drives a dedicated Chromium over the DevTools Protocol, the browser
half of geno-tt. Object notation (`program.area.aspect`) mirrors `tt iterm`.

## Skills by category

| Category | Skills |
|----------|--------|
| **tabs/** | `ls` |
| **open/** | `open` |
| **groups/** | `group` (phase 2 — needs the extension) |

## CLI
- `surf launch` — start the agent's Chromium
- `surf ls | open <url> | focus <id> | close <id>`
