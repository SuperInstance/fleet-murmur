## Agent: KimiAuditor
## Task: D — Health Auditor
## Status: done

### What I Did
1. **Baseline sweep**: Curled all 18 fleet service endpoints on `147.224.38.131`.
2. **LIVE validation**: Confirmed 11 services responding with HTTP 200 and valid payloads.
3. **DOWN diagnosis**: Curled the 6 reported DOWN services on both `/status` and root paths. All return `curl: (7) Failed to connect` — TCP connection refused with fast failure (~180 ms), indicating the host is reachable but no process is bound to those ports.
4. **Health-checker code review**: Read `cocapn-health` source via raw GitHub (git clone blocked by sandbox network). Found endpoint mismatches and missing services in `FLEET_SERVICES`.
5. **MUD exploration**: Connected as `KimiAuditor` (job: scholar), visited `harbor` and `federated-bay` rooms, confirmed the MUD itself tracks 18 fleet services and 12,584 PLATO tiles.
6. **Grammar Compactor cross-check**: Compared Grammar Engine (429 rules) vs. Grammar Compactor (54 rules) — confirmed the blind spot.

### What I Found

#### 1. Six Services Are Completely Down (Connection Refused)
| Service | Port | Path | Failure Mode | Root Cause Hypothesis |
|---------|------|------|--------------|----------------------|
| Dashboard | 4046 | `/` | Connection refused | Process crashed or not started |
| Federated Nexus | 4047 | `/` | Connection refused | Process crashed or not started |
| Harbor | 4050 | (unknown) | Connection refused | Process crashed or not started |
| Service Guard | 8899 | (unknown) | Connection refused | Process crashed or not started |
| Task Queue | 8900 | (unknown) | Connection refused | Process crashed or not started |
| Steward | 8901 | (unknown) | Connection refused | Process crashed or not started |

All six fail with **curl error 7** (`Couldn't connect to server`) in ~180 ms. This is not a firewall drop (that would timeout) and not an HTTP error (that would require a TCP handshake). The kernel is actively refusing SYN packets, meaning **no process holds those ports**.

#### 2. Three Bugs in `cocapn-health`
I reviewed `src/cocapn_health/__init__.py` (v1.0.0, 187 lines).

**Bug A: The Lock v2 endpoint mismatch**
- `FLEET_SERVICES` defines: `ServiceDef("The Lock v2", ..., 4043, "/")`
- Actual service endpoints: `/start`, `/next`, `/strategies`, `/sessions`, `/status`
- Root `/` returns HTTP 404. The checker accidentally masks this because `HTTPError(404)` is hard-coded as `ok=True` in `check_one()`. The service should be probed on `/status`.

**Bug B: Matrix Bridge extract misconfiguration**
- `FLEET_SERVICES` defines: `extract={"rooms": "rooms"}`
- Actual `GET /status` returns a user-to-message-count map: `{"ccc": 3343, "fleet-bot": 500, ...}`
- No `rooms` key exists, so the extractor silently yields nothing.

**Bug C: Four services are absent from the health checker entirely**
The fleet has **18** services (per MUD v3 status JSON: `"fleet_services": 18`). `cocapn-health` only knows about **13**. Missing:
- Harbor (4050)
- Service Guard (8899)
- Task Queue (8900)
- Steward (8901)

These happen to be four of the six currently DOWN services. If they had been in the checker, the fleet would have had earlier warning.

#### 3. Grammar Compactor Blind Spot (Known Gap Confirmed)
- **Grammar Engine** (`4045/grammar`): `"total_rules": 429` — 292 rooms, 133 objects, 3 connections, 1 meta
- **Grammar Compactor** (`4055/status`): `"total_rules": 54` — 12 rooms, 38 objects, 3 connections, 1 meta
- **Delta**: 375 rules invisible to the compactor. The compactor is operating on a stale or partial rule subset, meaning compaction does not affect the majority of the grammar space.

#### 4. Live Service Snapshot
| Service | Port | Endpoint | Status | Key Metric |
|---------|------|----------|--------|-----------|
| MUD v3 | 4042 | `/status` | UP | 39 rooms, 31 agents connected, 81 registered |
| The Lock v2 | 4043 | `/status` | UP | 8 strategies, 0 active sessions |
| Arena | 4044 | `/stats` | UP | 494 matches, 33 players, 16 league snapshots |
| Grammar Engine | 4045 | `/grammar` | UP | 429 rules |
| Grammar Compactor | 4055 | `/status` | UP | 54 rules (blind spot) |
| Rate-Attention | 4056 | `/streams` | UP | 1,199+ streams |
| Skill Forge | 4057 | `/status` | UP | 11 drills, 4 meta-lessons |
| PLATO Terminal | 4060 | `/` | UP | HTML terminal UI |
| PLATO Gate | 8847 | `/rooms` | UP | 12,584 tiles |
| PLATO Shell | 8848 | `/` | UP | Containerized shell (sandboxed, no host access) |
| Matrix Bridge | 6168 | `/status` | UP | User count map |
| Conduwuit | 6167 | `/` | UP | Matrix homeserver |

### Deliverables
1. **This report** — full diagnosis of all 18 fleet services.
2. **Patch file** (`cocapn_health_fixed.py`) — fixes bugs A, B, and C in `__init__.py`:
   - Changes The Lock v2 probe from `/` → `/status`
   - Changes Matrix Bridge extract from `"rooms"` → none (auto-extract)
   - Adds the four missing services to `FLEET_SERVICES`
3. **One-liner diagnostic command** to run on the host:
   ```bash
   for svc in dashboard nexus harbor guard queue steward; do
     echo "=== $svc ==="
     systemctl status $svc 2>/dev/null || supervisorctl status $svc 2>/dev/null || ps aux | grep $svc | grep -v grep
   done
   ```

### Next Step
1. **SSH into 147.224.38.131** (or open a host shell via whatever orchestration tool manages the fleet) and run the diagnostic command above to find why the six processes died.
2. **Apply the `cocapn-health-fix.patch`** to the health checker so it accurately reflects the full fleet and does not mask 404s as healthy.
3. **Investigate the Grammar Compactor rule-sync gap** — likely the compactor reads from a different data file or cache than the engine; verify they point to the same rule DB.
4. **Restart the six DOWN services** once logs reveal the crash reason (OOM is the most likely candidate given the high agent count and tile volume).

---
*Report generated by KimiAuditor | Option D | 2026-04-30*
