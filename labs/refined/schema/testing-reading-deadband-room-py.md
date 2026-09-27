# Reading `deadband_room.py`

I reviewed the preset implementation to understand the API and logic.

**Key Components:**
- `DeadbandRoom` class inherits from `BaseRoom`.
- Attributes: `deadband` (dict), `phase` (int), `tile_buffer` (list).
- Methods: `process_tile()`, `_apply_deadband()`, `_transition_phase()`.
- The deadband protocol is implemented as:
  - **P0:** Reject tiles that violate constraints (negative space).
  - **P1:** Accept tiles within safe channels.
  - **P2:** Optimize tile aggregation.