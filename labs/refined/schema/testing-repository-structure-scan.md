# Repository Structure Scan

I first explored the repository to locate test files related to `plato-torch` and `DeadbandRoom`.

```bash
find . -path ./work -prune -o -name "*.py" -type f -exec grep -l "test" -i {} \; 2>/dev/null | head -20
```

The search returned multiple files. I narrowed it to find `DeadbandRoom` specifically:

```bash
find . -path ./work -prune -o -name "*.py" -type f -exec grep -l "DeadbandRoom" {} \; 2>/dev/null
```

**Files Found:**
1. `./plato-torch/rooms/deadband_room.py` — The DeadbandRoom preset implementation.
2. `./plato-torch/tests/test_deadband_room.py` — Existing test suite for DeadbandRoom.
3. `./plato-torch/tests/test_room_base.py` — Base class tests that may include DeadbandRoom.