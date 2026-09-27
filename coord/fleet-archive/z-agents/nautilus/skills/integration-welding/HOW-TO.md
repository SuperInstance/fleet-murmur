# How to Bridge Standalone Modules into Working Systems

## The Problem

The fleet accumulates standalone modules — each fully functional in isolation, none wired together. `holodeck-studio` is the canonical example: 27 Python files, 12 of which define complete subsystems (cartridge bridge, fleet scheduler, tender fleet, constructed NPCs, adventure system, session recorder, perception, instinct, etc.), but only `server.py` actually runs. The rest are imported and used only if `patch_handler()` connects them.

## The Three-Layer Architecture

When analyzing a fleet repo, you'll typically find:

1. **Working Foundation** — The code that runs today. In holodeck-studio, this is `server.py` (MUD server on port 7777). It handles TCP connections, agent lifecycle, room navigation, and basic commands.

2. **Next-Gen Design** — Modules that implement ambitious features but aren't connected. `lcar_scheduler.py` (model scheduling), `lcar_tender.py` (cloud-edge message passing), `agentic_oversight.py` (agent monitoring), `perception_room.py` (environmental awareness).

3. **Demo Layer** — Scripts that showcase features in isolation. `demo_holodeck.py`, `seed_world.py`. Useful for validation, not for production.

The integration task: pull modules from layer 2 into layer 1 without breaking layer 1.

## The Wiring Pattern: import, attach, register, test

### Step 1: Import

```python
# In your integration module (e.g., mud_extensions.py)
from lcar_cartridge import CartridgeBridge
from lcar_scheduler import FleetScheduler
from lcar_tender import TenderFleet
```

### Step 2: Attach

Attach subsystems as class attributes on the handler:

```python
def patch_handler(CommandHandler):
    CommandHandler.cartridge_bridge = CartridgeBridge()
    CommandHandler.scheduler = FleetScheduler()
    CommandHandler.tender_fleet = TenderFleet()
    CommandHandler.constructed_npcs = {}
    CommandHandler.repo_rooms = {}
    CommandHandler.adventures = {}
    CommandHandler.recorder = SessionRecorder()
```

This makes them accessible from any command method via `self.scheduler`, `self.tender_fleet`, etc.

### Step 3: Register

Add command handlers to the handler's dispatch table:

```python
CommandHandler.new_commands = {
    "cartridge": CommandHandler.cmd_cartridge_ext,
    "scene":     CommandHandler.cmd_scene_ext,
    "schedule":  CommandHandler.cmd_schedule_ext,
    "tender":    CommandHandler.cmd_tender_ext,
    "summon":    CommandHandler.cmd_summon_ext,
    "adventure": CommandHandler.cmd_adventure_ext,
    # ...
}
```

The base `handle()` method in `server.py` already checks `self.new_commands` as a fallback:

```python
handler = handlers.get(cmd)
if not handler:
    handler = self.new_commands.get(cmd) if hasattr(self, 'new_commands') else None
```

### Step 4: Test

Wire the same `patch_handler()` call in your test fixtures:

```python
@pytest_asyncio.fixture
async def handler(world):
    patch_handler(CommandHandler)  # same call as production
    return CommandHandler(world)
```

Now every extension command is testable:

```python
@pytest.mark.asyncio
async def test_schedule_status(self, handler, agent):
    await handler.handle(agent, "schedule")
    assert "Fleet Scheduler" in agent.writer.get_text()
```

## The patch_handler Pattern

`patch_handler()` from `mud_extensions.py` is the fleet's standard integration mechanism. It:

1. Imports subsystem modules (gracefully handles missing deps)
2. Calls `_attach_extension_methods(CommandHandler)` which defines ~25 async methods and attaches them as class attributes
3. Instantiates subsystems as class-level singletons
4. Builds the `new_commands` dispatch dict
5. Prints a status summary

This pattern is repeatable. Any new subsystem gets: a module file, methods attached in `_attach_extension_methods`, subsystem instance in `patch_handler`, command string in `new_commands`, tests in `test_server.py`.

## Key Principle

**One wiring point.** The fleet should have exactly one place where all subsystems are connected. If you find wiring scattered across 5 files, consolidate it. A single `patch_handler()` (or equivalent) means any agent can read one function and understand the entire integration surface.
