# geno-surf — Chromium orchestration for the geno agent

`geno-surf` is the `surf` CLI: the **browser half of [geno-tt](https://github.com/42euge/geno-tt)**.
Where `tt iterm` drives iTerm2, `surf` drives a dedicated Chromium over the
DevTools Protocol — addressed by the **same object-notation registry**
(`ngrt.main.tickets`, `hil.plans`, `bluebeam.vanteon`, …).

## The split: Safari human, Chromium agent

Safari has **no scriptable Tab Groups** (not in AppleScript, not in its
WebExtension API) — so it stays your hand-curated space. The **agent** drives a
separate **Chromium** (Chrome/Chromium/Brave/Arc) launched with remote
debugging under its own profile (`~/.geno/surf/chrome-profile`). The two never
collide.

## Object notation (shared with geno-tt)

```
<program>.<area>.<aspect>       e.g. ngrt.main.tickets, hil.plans
```
A node addresses a bundle of context across surfaces: an iTerm pane/tab (geno-tt)
**and** a set of browser tabs/group (geno-surf). One registry, many adapters.

## Commands (v0.1 — CDP HTTP, dependency-free)

```
surf launch                 start the agent's Chromium (remote debugging)
surf ls                     list open tabs (id · title · url)
surf open <url> [--group G] open a tab
surf focus <id> | close <id>
surf group <name.path> …    (phase 2 — see below)
```

## Architecture & the tab-group decision

CDP manages **targets (tabs), navigation, and windows** — but **NOT** Chrome's
native **Tab Groups**, which are the `chrome.tabGroups` extension API. So:

- **Phase 1 (this):** CDP HTTP endpoints (`/json/list|new|activate|close`) via
  stdlib `urllib`. List/open/focus/close tabs. Core stays dependency-free.
- **Phase 2:** deeper control via CDP websockets (`websocket-client`, the `cdp`
  extra) — navigation events, window arrangement (model a node as a window).
- **Phase 3:** native Tab Groups via a bundled **geno-surf extension**
  (`chrome.tabGroups`) + a native-messaging bridge to the registry — for true
  bidirectional group sync matching the grouped look.

## Registry (source of truth)

The object-notation tree is shared with geno-tt (planned: `~/.geno/registry.yaml`).
Editing it re-syncs every surface; each surface (iTerm, Chromium) is a thin adapter.

## Repo structure

```
geno-surf/
├── GENO.md · README.md · SKILL.md
├── pyproject.toml            # `surf` entry point; core deps = []
├── geno_surf/
│   ├── cli.py                #   dispatch (main(argv)->int)
│   └── chrome_cdp.py         #   DevTools Protocol HTTP client (stdlib)
├── .claude-plugin/{plugin,marketplace}.json
└── skills/<category>/<name>/SKILL.md
```

## Conventions
- Mirrors geno-tt: dependency-free core, optional extras, `skills/<cat>/<name>/SKILL.md`
  named `geno-surf-<cat>-<name>`. Bump version in `pyproject.toml`, `genotools.yaml`,
  `geno_surf/__init__.py`, and the plugin/marketplace manifests.
