# Understanding Test Patterns (Based on Fleet Context)

From FLEET-CONTEXT.md, I understand:

### Key Technologies Relevant to Testing:
1. **plato-torch**: 25 training room presets, self-training rooms
2. **Deadband Protocol**: P0 (avoid), P1 (safe channels), P2 (optimize)
3. **Ghost tiles**: Dead agents' lessons as P0 knowledge

### Expected Test Patterns:
1. **P0 Tests**: Should test negative cases - what should NOT happen
2. **P1 Tests**: Should test boundary conditions - safe operation ranges  
3. **P2 Tests**: Should test optimization paths - best performance scenarios
4. **Integration Tests**: How rooms interact with ensign exports
5. **Edge Cases**: Mirror play, ghost tile handling, shell bootstrapping