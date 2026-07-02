---
name: geno-surf-groups-group
description: >-
  Open URLs into a native Chrome tab group named by object notation (program.area.aspect).
allowed-tools: "Bash(surf *)"
metadata:
  author: 42euge
  version: "0.2.0"
---

# surf groups/group

```
surf group <program.area.aspect> <url> [url…] [--color blue|red|…]
surf groups        # list existing groups
```

Opens each URL as a background tab inside a native Chrome tab group titled by the object path (created + colored if new). Requires the agent browser to be **Chrome for Testing** (`surf launch`) — stable Chrome 137+ blocks the bundled permissions extension. No window refocus.
