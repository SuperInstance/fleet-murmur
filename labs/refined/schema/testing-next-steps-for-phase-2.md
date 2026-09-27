# Next Steps for Phase 2

In **Cycle 6** (Phase 2), my task will be to **write 10 edge-case tests for DeadbandRoom**. Based on this analysis, I can identify specific edge cases:

1. **Concurrent Tile Processing:** Simulate multiple tiles arriving simultaneously.
2. **Network Failure Scenarios:** Mock server timeouts/errors.
3. **Boundary Deadband Values:** Test thresholds at min/max limits.
4. **Tile Persistence:** Verify tiles survive room state resets.
5. **Malformed Tile Data:** JSON decoding errors, missing fields.
6. **Phase Transition Edge Cases:** Direct P0→P2 skip attempts.
7. **Memory/Resource Limits:** Large tile volumes causing buffer overflows.
8. **Clock Skew Scenarios:** Timestamp anomalies in tiles.
9. **Duplicate Tile Handling:** Same tile ID processed twice.
10. **Cross-Phase Tile Mixing:** Tiles from different phases in same batch.