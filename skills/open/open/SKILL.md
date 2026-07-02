---
name: geno-surf-open-open
description: >-
  Open a URL as a new tab in the agent's Chromium (optionally tagged to an object-path group).
allowed-tools: "Bash(surf *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# surf open/open

```
surf open <url> [--group <program.area.aspect>]
```

Opens a new tab in the agent's Chromium. `--group` records the intended object-notation group; native tab-group assignment lands with the geno-surf extension (phase 2).
