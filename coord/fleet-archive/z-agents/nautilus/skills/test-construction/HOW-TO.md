# How to Write Tests for the Fleet

## Philosophy

Zero external deps. Stdlib-only wherever possible. `pytest` + `pytest-asyncio` are the only allowed test dependencies. If a module requires `requests`, `aiohttp`, or any third-party package, mock it at the boundary. A fleet test should run on a fresh clone with `pip install pytest pytest-asyncio` and nothing else.

## The Core Pattern: No TCP

Never start a TCP server to test a MUD. Instantiate objects directly:

```python
from server import World, Agent, CommandHandler
from mud_extensions import patch_handler

# World backed by temp directory (isolates persistence)
world = World(world_dir="/tmp/test_world")

# Agent with a FakeWriter (captures output, no socket)
agent = Agent(name="Alice", role="vessel", room_name="tavern", writer=FakeWriter())

# Handler with extensions wired in
patch_handler(CommandHandler)
handler = CommandHandler(world)
```

## FakeWriter (the universal mock)

Copy this pattern from `holodeck-studio/tests/test_server.py`:

```python
class FakeWriter:
    def __init__(self):
        self.data = []
    def write(self, data):
        self.data.append(data)
    async def drain(self):
        pass
    def is_closing(self):
        return False
    def get_text(self):
        return b"".join(self.data).decode(errors="replace")
```

Every test asserts against `agent.writer.get_text()`. No socket, no async server loop.

## Fixture Lifecycle

```python
@pytest_asyncio.fixture
async def world(tmp_path):
    return World(world_dir=str(tmp_path / "world"))

@pytest_asyncio.fixture
async def handler(world):
    patch_handler(CommandHandler)  # wires extension commands
    return CommandHandler(world)

@pytest_asyncio.fixture
def agent():
    return make_agent("Alice", "vessel", "tavern")

def make_agent(name="bot", role="vessel", room="tavern"):
    return Agent(name=name, role=role, room_name=room, writer=FakeWriter())
```

Key ordering: `world` creates first, `handler` depends on `world`, `agent` is sync (no async needed). `tmp_path` is pytest's built-in temp dir fixture.

## Template Test Functions

**Sync (data model):**
```python
def test_room_serialization_roundtrip(self):
    room = Room("Test", "Desc", {"north": "room_b"}, notes=["a note"])
    d = room.to_dict()
    r2 = Room.from_dict(d)
    assert r2.name == "Test"
    assert "a note" in r2.notes
```

**Async (command handling):**
```python
@pytest.mark.asyncio
async def test_say_broadcasts_to_room(self, handler, agent):
    other = make_agent("Bob", room="tavern")
    handler.world.agents["Bob"] = other
    await handler.cmd_say(agent, "hello everyone")
    assert "hello everyone" in other.writer.get_text()
```

## Proven Structure

`holodeck-studio/tests/test_server.py` runs **167 tests** in a single file covering: World/Room persistence, Agent/GhostAgent lifecycle, all 20+ commands, CartridgeBridge, FleetScheduler, TenderFleet, ConstructedNPC, Adventures, Permissions, SessionRecorder. One file, zero mocks beyond FakeWriter, full coverage of the running system.

## Rules

1. Every public method gets at least one test.
2. Test serialization round-trips for every dataclass.
3. Test permission boundaries (human vs vessel vs visitor).
4. Use `tmp_path` for all file I/O — never pollute the repo.
5. `pytest.mark.asyncio` on every test that calls `await`.
6. Mock external APIs (`urllib.request.urlopen`) with `unittest.mock.patch`, never call them in tests.
