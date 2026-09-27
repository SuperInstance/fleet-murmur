# How to Analyze Fleet Repos

## The Rapid-Parallel-Exploration Pattern

When diving into a new repo, launch 3-5 subagents simultaneously, each with a narrow focus:

| Subagent | Scope | Output |
|----------|-------|--------|
| #1 Architecture | File tree, imports, class hierarchy | Dependency graph |
| #2 Gaps | Functions defined but never called, TODO/FIXME | Gap list |
| #3 Tests | Test count, coverage holes, last run status | Test health |
| #4 Docs | README vs actual exports, stale references | Drift report |
| #5 Cadence | Git log (last 30 commits), commit frequency | Activity heatmap |

Each subagent reads 5-10 files max. Total wall time: ~60 seconds. You synthesize the outputs.

## What to Look For

**Architecture:** What's the entry point? What does `main()` import? Is there a single file that wires everything together, or is wiring scattered? Draw the dependency graph — the shape reveals the design intent.

**Orphaned modules:** Files that define classes/functions but are never imported by anything. In `holodeck-studio`, 12 of 27 modules were standalone — complete, tested internally, but never wired into `server.py`. That's the "implemented but not wired" antipattern.

**README drift:** Does the README mention commands, endpoints, or features that don't exist in the code? Does the code have features the README doesn't mention? Both are signals.

**Test coverage:** Count test files. Check if tests import from the modules they claim to test. A test file that only tests its own helpers isn't testing the system.

## Case Study: holodeck-studio Dual Architecture

`holodeck-studio` has two architectures coexisting:

1. **The MUD layer** (`server.py`): asyncio TCP server, World/Room/Agent model, command handler. This runs on port 7777 and works.

2. **The fleet integration layer** (12 modules): `lcar_cartridge.py`, `lcar_scheduler.py`, `lcar_tender.py`, `fleet_integration.py`, etc. These define the fleet's orchestration systems.

The bridge: `mud_extensions.py` defines `patch_handler(CommandHandler)` which monkey-patches extension commands onto the MUD's CommandHandler. `server.py:main()` calls `patch_handler(CommandHandler)` at startup. This is the single wiring point.

**The detection heuristic:** Search for `import` statements in entry points. If `server.py` doesn't import a module, that module is orphaned unless something imports it transitively. Trace the import chain.

## Detecting "Implemented But Not Wired"

```bash
# For each .py file, check if any other file imports it
for f in *.py; do
    module="${f%.py}"
    count=$(rg "import $module" --type py | wc -l)
    if [ "$count" -eq 0 ]; then
        echo "ORPHAN: $module"
    fi
done
```

Also check: functions defined in module files that are never called from the entry point. A module might be imported for its classes but its functions never invoked.

## Git Log Analysis

```bash
# Development cadence — commits per day, last 30 days
git log --since="30 days ago" --format="%ad" --date=short | sort | uniq -c | sort -rn

# Who's been active
git log --since="30 days ago" --format="%an" | sort | uniq -c | sort -rn

# Burst detection — biggest commit days
git log --since="30 days ago" --format="%ad" --date=short | uniq -c | sort -rn | head -5
```

High burst activity followed by silence often means a sprint-based agent. Steady daily commits mean a daemon-style agent. No commits in 14+ days means an inactive repo — flag it.

## Output Format

Synthesize into a structured report:
1. **Architecture diagram** (text-based, imports as edges)
2. **Health score** (tests pass? CI green? Recent commits?)
3. **Integration gaps** (what's implemented but not wired)
4. **Recommendations** (prioritized action items)
