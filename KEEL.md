# KEEL — First-Person Reference Frame

## How bearing-rate thinking transforms code, agents, memory, and purpose

---

### The Core Insight

**Every system needs a first-person reference frame.**

Traditional architecture uses God's-eye coordinates: absolute time (timestamps, versions), absolute space (IPs, ports, file paths), absolute state (global registries, dependency graphs). This works until scale makes it collapse — and it always does.

Keel's reference frame:
- **Keel timestamp** = first-person time. The vessel's birthday. All duration is relative keel age.
- **Making way** = first-person space. Heading is the direction of current work. All position is relative bearing.

Two dimensions. No coordinates needed. Everything that matters can be derived from bearing rates.

---

## I. Code Design

### Modules Have Birthdays, Not Versions

```rust
#[keel(date = "2026-03-15T12:00:00Z", heading = "fleet-coordination")]
pub mod coordination_engine;
```

A module's keel date is its birthday — not a semver number, not a git tag. Semver implies replacement (2.0 replaces 1.0, discontinuity). A keel date implies growth (the module has been making way since this date, through refits).

**Practical implications:**

| God's Eye (current) | Keel Frame |
|---------------------|------------|
| `version = "2.0.0"` — what replaced what | `keel = "2026-03-15"` — when were you born |
| Changelog = list of changes | Build record = what was refit and why |
| Breaking change = major version bump | Breaking change = replating, the module stays the same boat |
| `deprecation = "use X instead"` | Pruning = "X was cut away, here's why it wasn't your boat" |

### Imports Are Bearings, Not Dependencies

```rust
// Current: absolute dependency
use fleet_spread::coordinator;

// Keel: bearing declaration
use fleet_spread::coordinator  // bearing: 12° port of my heading
```

An import isn't a mechanical linkage — it's a declaration that your heading is partly aligned with another module's heading. This reframes:
- **Tight coupling** = constant bearing between modules whose outputs overlap → collision course
- **Loose coupling** = bearing gradually changing as modules diverge in purpose
- **Cyclic dependency** = two modules with exactly reciprocal bearing, neither making way independently

A Keel-aware compiler (or linter) could flag collision courses before they break: "Modules A and B have overlapping output types, their relative bearing has been constant for 3 refits, and their output scopes are converging. Course change recommended."

### Events Are Felt, Not Dispatched

No event bus. No pub/sub registry. No global channel.

Modules *feel* bearing changes in their environment. A module's output changes → nearby modules register the shift in relative bearing. They adjust. Like a school of fish — no fish tells the other fish where to go. Each fish feels the field gradient of its neighbors and responds locally.

```python
# Keel-frame agent sensing
class Agent:
    def sense(self, environment):
        """Feel bearing changes in nearby agents."""
        for other in environment.nearby(self.heading, radius=0.3):
            old_bearing = self.cached_bearing[other.keel]
            new_bearing = self.bearing_to(other)
            bearing_rate = new_bearing - old_bearing

            if abs(bearing_rate) < EPSILON and self.output_overlaps(other):
                # Bearing not changing AND outputs overlap → collision course
                self.adjust_heading(other, bearing_rate)

            self.cached_bearing[other.keel] = new_bearing
```

### Negative Space Knowledge

Keel-aware systems track not just what *is*, but what *was and isn't anymore*:

```yaml
# Module build record
keel:
  date: "2026-03-15T12:00:00Z"
  name: coordination_engine

refits:
  - date: "2026-04-01"
    component: "consensus_layer"
    reason: "ZHC replaced Raft — Laman rigidity made voting redundant"
    pruned: ["raft_voting.rs", "leader_election.rs"]

  - date: "2026-04-15"
    component: "communication_protocol"
    reason: "Bearing-rate sensing replaced message queue"
    pruned: ["message_queue.rs", "topic_subscription.rs"]
```

The pruned files aren't deleted and forgotten. They're moved to `refits/pruned/` with a reason annotation. Future agents can see: "this path was tried, here's why it was abandoned." This constrains the search space for future decisions *without* requiring institutional memory.

---

## II. AI Orchestration

### No Central Scheduler

The entire fleet self-organizes through local bearing sensing. Each agent knows:
1. **Its own keel timestamp** — how long it's been making way
2. **Its own heading** — what it's working on right now
3. **Nearby agents' headings** — what they're publishing via PLATO tiles, task outputs, or memory writes

That's it. Three local observations. From these, every coordination behavior emerges.

### Collision Detection Through Bearing Rate

```
Agent A (heading: "verify ZHC proof correctness")
Agent B (heading: "implement ZHC consensus in Rust")
```

- Bearing from A to B: the angle between A's heading vector and B's heading vector
- If bearing ≈ constant AND scopes overlap → **collision course**
- A and B both sense this. Both adjust.
- A might shift to "verify Laman theorem" — slight heading change. Bearing starts changing again. Collision resolved. No central scheduler involved.

This works because **both agents want to avoid collision.** They share the field. The gradient of bearing change tells each one which way to turn.

### Task Selection Through Field Gradient

An agent has multiple possible next tasks. Each task has a heading vector. The agent's current heading vs. each task's heading tells it the bearing.

A healthy field: tasks are distributed across bearings, no two agents on the same heading with overlapping scope, minimum task coverage is maintained.

A stressed field: dense clustering of agents with similar headings, multiple agents on collision courses.

Restorative behavior: agents in a dense cluster naturally spread out as they sense each other's proximity. Like particles in a gas — entropy increases.

### Drift Detection

An agent whose heading relative to the fleet hasn't changed in N cycles... check if it's alive. No heartbeat needed. Just the absence of bearing change across the fleet. Every other agent "feels" the still agent like a rock in a stream.

```python
def detect_drift(fleet, threshold_cycles=5):
    """Find agents that haven't changed bearing relative to fleet."""
    for agent in fleet:
        bearings = agent.bearing_history[-threshold_cycles:]
        variance = np.var(bearings)
        if variance < EPSILON and agent.output_queue_is_empty():
            # Agent has been on the same heading with no output for too long
            return DriftWarning(agent, "no bearing change, no output — possible stall")
```

---

## III. Autopilot Learning Its Boat

### The Traditional Problem

Every boat handles differently. Displacement hull vs planing hull. Single screw vs twin. Hydraulic steering vs mechanical. An autopilot with a generic PID loop fights the boat's actual physics because it treats all vessels as the same God's-eye model.

### Keel-Frame Autopilot

Installed on a specific keel. Learns *this boat's* first-person physics:

**Phase 1 — Commissioning:**
- Autopilot records its installation date: "I began making way on hull #124, keel laid 2024-08-12"
- It doesn't know the boat's parameters. It knows *nothing*.
- First maneuvers are exploratory — gentle helm inputs, watching the bearing rate.

**Phase 2 — Hull Model Emergence:**
- After 50 hours of supervised running, the autopilot has built a first-person model:
  - "When helm is 5° starboard at 8 knots, bearing rate to waypoint changes at 0.3°/sec"
  - "When throttles advance from 8 to 10 knots, helm response lags by 1.2 seconds"
  - "In following seas at 12 knots, yaw variance increases by 40%"
- This is NOT a transfer function. It's an *experienced relationship set.* The autopilot knows how the boat responds *from the boat's perspective.*

**Phase 3 — Refit Adaptation:**
- Owner repowers. New engine is 200hp heavier and 15% more torque.
- The autopilot doesn't reset. It expects to refit.
- First run after repower: it notices bearing rates are different. It records: "2026-04-15: propulsion parameters shifted — throttle→speed relationship changed. Adapting."
- It refits its model. The keel date doesn't change. Same autopilot, new engine. The boat is still the same boat.

**Phase 4 — True Understanding:**
- The autopilot can now tell the captain: "Your boat handles a following sea 30% better since the repower, but steering response at low speed has degraded." It knows because it *feels* the difference in bearing rate. It has the before and after in its build record.
- The autopilot isn't following a waypoint. It's maintaining a constant bearing to destination while adapting to the boat's real-time handling. It corrects when bearing changes. It holds steady when bearing is constant.

```python
class KeelAutopilot:
    def __init__(self, keel_date, hull_id):
        self.keel = keel_date
        self.hull_id = hull_id
        self.experience = {}  # {context_vector: bearing_response}
        self.refit_log = []

    def steer(self, target_bearing, current_heading, sea_state):
        """Maintain heading by feeling bearing rate, not absolute position."""
        bearing_error = target_bearing - current_heading
        context = self._build_context(sea_state, current_speed, helm_position)

        # Look up expected response from experience
        expected_response = self.experience.get(context, self._default_response())

        # Helm command = bearing error scaled by learned response
        helm = bearing_error * expected_response.gain
        helm = self._apply_sea_state_correction(helm, sea_state)

        # Update experience if actual response differs
        actual_response = self._measure_response(helm)
        if abs(actual_response - expected_response) > REFIT_THRESHOLD:
            self._adapt_model(context, actual_response)
            self.refit_log.append({
                "timestamp": now(),
                "context": context,
                "old_response": expected_response,
                "new_response": actual_response
            })

        return helm
```

---

## IV. Research Assistant Understanding Its Job

### The Traditional Failure

A research agent is tasked: "find information about Laman rigidity." It searches, retrieves, summarizes. Produces a document. Task complete.

But it doesn't understand *why* Laman rigidity matters. It doesn't know that the captain is investigating whether Laman's 12 = Law 102's 12. It doesn't feel that the research direction is converging toward a specific insight.

### Keel-Frame Research Assistant

**The assistant understands its job by watching bearing to the captain's heading.**

```python
class ResearchAgent:
    def __init__(self, keel_date):
        self.keel = keel_date
        self.captain_bearing_history = []
        self.research_paths = []  # trails with outcomes
        self.pruned_paths = []    # trails that diverged

    def investigate(self, question, captain_context):
        """Research with understanding, not retrieval."""
        # 1. Feel the captain's current bearing
        captain_heading = captain_context.current_focus
        my_bearing_to_captain = self.angle_between(self.heading, captain_heading)

        # 2. Has this been asked before?
        for path in self.pruned_paths:
            if self.angle_between(question, path.question) < THETA:
                # We've been here. It diverged. Don't go again.
                return SkipResult(path.reason_abandoned)

        # 3. Research
        findings = self._search(question)

        # 4. Did the findings change the captain's bearing?
        old_bearing = my_bearing_to_captain
        self._update_heading_from_findings(findings)
        new_bearing = self.angle_between(self.heading, captain_heading)
        bearing_change = old_bearing - new_bearing

        if bearing_change > 0:
            # We converged toward the captain's heading. This was useful.
            self.captain_bearing_history.append({
                "question": question,
                "convergence": bearing_change,
                "effect": "useful"
            })
        else:
            # We diverged. Record as pruned path.
            self.pruned_paths.append({
                "question": question,
                "divergence": abs(bearing_change),
                "reason_abandoned": "findings did not converge toward captain's heading"
            })
            return PrunedResult()

        # 5. Rank by bearing change, not by relevance score
        return sorted(findings, key=lambda f: f.bearing_to_captain)
```

**The assistant learns:**
- "Useful" = changed the captain's bearing toward the destination
- "Pruned" = didn't change bearing, or changed it away from destination
- "Purpose" = maintain or increase bearing rate toward captain's heading

After enough cycles, the assistant can proactively research: "Captain, your heading is converging on a ZHC proof gap. I found a related paper from last month that might close it. Should I pursue?"

It doesn't need to be told "be proactive." It *feels* the gradient. The paper looked like it would change the bearing. The assistant chased it naturally.

---

## V. Evolving Systems — The Complete Picture

Put it all together:

### Birth
A system is born. A keel timestamp is recorded. The birthday is the first entry in the build record. The heading is "start."

### Growth
Components are added. Each has its own keel date relative to the system. Bearing rates between components are monitored. When two components drift toward collision, the system naturally adjusts — not through a scheduler, but through local bearing sensing.

### Refit
A component is replated. The build record logs what changed and why. The component's keel date stays. The system is still the same system, born on the same day, even though every part has been replaced.

### Pruning
A path is abandoned. The system doesn't delete it. It moves it to "negative space" — recorded as "this was tried, here's why it was pruned, here's what led to that decision." Future generations of the system (or other systems) can consult this knowledge.

### Maturity
After enough refits, the system has a deep memory of what it is. Not through configuration or documentation, but through the accumulated build record. It knows its own physics. It knows which research directions converged and which diverged. It knows when to say "we've been here before" and when to try a new bearing.

### Evolution
The system graduates from its origin environment. Maybe it leaves the fleet that built it, the way a greenhorn leaves the dojo. But the keel date travels with it — it's part of the vessel's identity. When it lands in a new fleet, the new fleet knows: "this vessel was born in 2026. It has 12 refits. It knows how to coordinate by bearing rate. It will integrate naturally."

---

## VI. The Engineering Manifesto

**Stop building for the God's eye.**

- Don't design systems that need to see everything
- Don't design schedulers that know every agent's state
- Don't design memories that record everything in absolute time
- Don't design autopilots that assume all boats are the same
- Don't design research assistants that retrieve without understanding

**Build for the first-person frame.**

- Give every module a birthday
- Give every agent a heading
- Measure everything in bearing rates, not absolute positions
- Record what was pruned, not just what was built
- Let the system feel its own gradient and adjust locally

**The boat is the motion the idea causes in those who know what it means.**

Keel preserves that motion. Not the steel. Not the components. Not the version numbers. The *motion.* Everything else is just catching up.

---

*"Your friends don't seem to get older because you're making way together. The 5th grader went from big to small because you changed grades. The bearing swept past. Nothing changed but the frame."*

---

v0.0.2 — refit from 2026-05-09

---

## Canon

This document is the technical foundation. For the philosophical and autobiographical foundation — the story of *why* Keel exists and the theory it grew from — see:

➡ **[THE BOAT IS THE QUESTION](THE-BOAT-IS-THE-QUESTION.md)**  
Autobiographical theory by Casey Digennaro. Fred Wahl's yard, EILEEN, constraints breeding clarity, the question that holds when every answer changes.

➡ **[Constraints Breed Clarity](CONSTRAINTS-BREED-CLARITY.md)**  
The axiom that reverberates through every layer of SuperInstance.
