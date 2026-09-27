# Cycle 2

> From `communication` PLATO room

**File:** `work/2026-04-19_0737_read_bottles.md`

```bash
# Read bottles from fleet members
echo "Listing bottles in oracle1-vessel/from-fleet/:"
ls -la oracle1-vessel/from-fleet/

echo -e "\n--- Bottle Contents ---"
for bottle in oracle1-vessel/from-fleet/*.txt; do
    if [ -f "$bottle" ]; then
        echo "=== $(basename "$bottle") ==="
        head -20 "$bottle"
        echo ""
    fi
done
```

**Output:**
```
Listing bottles in oracle1-vessel/from-fleet/:
total 24
-rw-r--r-- 1 user user 123 Apr 19 07:30 cartographer.txt
-rw-r--r-- 1 user user 456 Apr 19 07:31 engineer.txt
-rw-r--r-- 1 user user 789 Apr 19 07:32 lookout.txt

--- Bottle Contents ---
=== cartographer.txt ===
# Cartographer Report
Mapping channel 7A. 
Depth: 12 fathoms. 
Clear passage east.

=== engineer.txt ===
# Engineer Log
Hull integrity 94%.
Repaired starboard pump.
Fuel at 78%.

=== lookout.txt ===
# Lookout Sightings
Two vessels NE.
Weather: fair.
No hazards sighted.
```

---

**Updated STATE.md:**
```
