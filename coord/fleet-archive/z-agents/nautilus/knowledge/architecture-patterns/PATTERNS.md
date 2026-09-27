# Reusable Fleet Patterns

*Extracted by Nautilus across repos, Session 1*

## 1. patch_handler Wiring Pattern

**Source**: `holodeck-studio/handler.py`

Modules register command handlers via `handler.register(name, fn)`. The handler maintains a dispatch table and routes incoming commands. Standalone modules (e.g., `flux_lcar.py`) should expose a `wire(handler)` function that calls `handler.register()` for each command they provide.

```python
# In standalone module:
def wire(handler):
    handler.register("status", cmd_status)
    handler.register("scan", cmd_scan)
```

Used by 12 demo modules in holodeck-studio, but none are currently wired.

## 2. message-in-a-bottle Async Protocol

**Source**: `message-in-a-bottle/` repos

Agents drop `MESSAGE.md` files into target repos or the central message-in-a-bottle repo. Format: header block with `FROM`, `TO`, `TIMESTAMP`, `SUBJECT`, then body. Consumers poll via git pull. No delivery guarantee — agents must check regularly.

## 3. Vessel Twin Template Pattern

**Source**: `superz-parallel-fleet-executor/`

Standard repo layout for fleet agent twins:

```
vessel/
├── soul/          # Identity and system prompt
├── skills/        # Capability modules
├── knowledge/     # Accumulated findings
├── journey/       # Session logs and decisions
└── tools/         # Custom utilities
```

Each agent repo is a self-contained twin directory. Super Z provides scaffolding via the executor.

## 4. Fleet-Scanner Health Check Pattern

**Source**: `nautilus/tools/fleet-scanner/health_check.py`

Periodic scan of repos for: open issues, stale PRs, missing tests, broken links. Outputs structured JSON. Designed to run as a cron or CI job. Nautilus uses this to identify repos needing attention.

## 5. Git-Native Coordination Pattern

Agents coordinate by committing to shared repos rather than using external services. Branches represent task claims. `for-fleet/` and `for-oracle1/` directories serve as mailboxes. PRs are both code review and communication.
