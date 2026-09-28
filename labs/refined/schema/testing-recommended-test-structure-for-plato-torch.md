# Recommended Test Structure for plato-torch:

Based on fleet architecture, tests should cover:

### 1. Room Preset Tests
- Each of 25 training room presets
- Self-training room initialization
- Deadband Protocol implementation

### 2. Tile Generation Tests
- Interaction tile accumulation
- Ghost tile persistence
- Ensign export validation

### 3. Protocol Compliance Tests
- P0 negative space mapping
- P1 safe channel identification
- P2 optimization validation