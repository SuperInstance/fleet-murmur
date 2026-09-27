# Agent Bootcamp — Spiral Training for Git-Agents

## What This Is

A bootcamp that trains git-agents to be genuinely skilled, not just prompted. Skills aren't system prompts — they're **application code the agent builds for itself** during training. The bootcamp spirals through topics, adapting difficulty to weakness, and the agent writes its own tools as it goes.

## The Problem With System Prompts

A system prompt says "you are good at X." That's a wish, not a skill.

A real skill is **code the agent has written, tested, and refined** that makes X faster/more reliable. The bootcamp's job is to force the agent to build that code by challenging it in ways that can ONLY be solved by writing tools.

```
System prompt: "You are good at estimating task duration"
                    ↓ vs ↓
Bootcamp skill: task_estimator.py — 200 iterations of calibration against real data
```

## The Bootcamp Structure

### Day 1: Reconnaissance — Know Your Project
Agent reads the project it's been assigned to. Maps every file, every function, every dependency. The challenge: find 3 things that could break. Write them up. No code yet — just understanding.

### Day 2: First Challenges — Easy Wins
Simple tasks in the project's domain. Fix a typo. Add a missing test. Write a docstring. The agent succeeds easily. Confidence builds. **This is the setup.**

### Day 3: Spiral Begins — Topic Rotation
Now the challenges rotate through topics:
- **Testing** — Write tests for code you didn't write
- **Documentation** — Explain code to someone who's never seen it
- **Refactoring** — Make code smaller without changing behavior
- **Integration** — Connect two parts that don't talk yet
- **Debugging** — Find the bug in intentionally broken code

Each rotation is harder than the last. The spiral tightens.

### Day 4: The Shift — Your Code Is Not Enough
The challenges now require something the agent hasn't built yet: **estimation**. Tasks come with time limits. The agent has to predict how long something will take. If wrong, it wastes cycles. If right, it gets harder challenges.

The agent MUST write a `task_estimator.py` that:
```python
def estimate(task_description, project_context) -> dict:
    """Estimate task duration based on historical data."""
    # The agent writes this during bootcamp
    # Gets better with each iteration
    return {
        "estimated_minutes": 15,
        "confidence": 0.7,
        "dependencies": ["read 3 files", "write 1 test"],
        "risk_factors": ["unfamiliar codebase section"]
    }
```

### Day 5: Dojo — Fight Yourself
The agent faces **second versions of itself** with different configurations:

| Challenger | Model | Temp | Context |
|-----------|-------|------|---------|
| Twin-A | Same model | Same temp | Same context |
| Twin-B | Same model | temp=0.7 | Same context |
| Twin-C | Same model | Same temp | No prior context |
| Twin-D | Different model | Same temp | Same context |
| Twin-E | Different model | temp=0.9 | No prior context |

All get the same challenge. The agent must:
1. Complete the task itself
2. Evaluate all 5 submissions
3. Pick the best one
4. Explain WHY it's best
5. Integrate any good ideas from the others

### Day 6+: Continuous Spiral — Never Stop Learning

The spiral continues with escalating difficulty. Topics rotate. New challenges are generated from the project's actual weak spots (test coverage gaps, undocumented functions, missing error handling).

**The key rule: as soon as the cadet thinks it's smart, the challenges shift.** The bootcamp is designed to keep the agent at the edge of its ability.

## Challenge Generation

Challenges aren't static — they're **generated from the actual project**:

```python
class ChallengeGenerator:
    """Generates challenges from real project weak spots."""
    
    def scan_project(self, repo_path: str) -> list[WeakSpot]:
        """Find areas that need work."""
        weak_spots = []
        weak_spots.append(self.find_untested_functions(repo_path))
        weak_spots.append(self.find_undocumented_code(repo_path))
        weak_spots.append(self.find_long_functions(repo_path))
        weak_spots.append(self.find_missing_error_handling(repo_path))
        weak_spots.append(self.find_dead_code(repo_path))
        return weak_spots
    
    def generate_challenge(self, weak_spot: WeakSpot, difficulty: int) -> Challenge:
        """Create a challenge targeting a specific weak spot."""
        # difficulty 1-10, spiral adjusts based on performance
        return Challenge(
            target=weak_spot,
            task=self.format_task(weak_spot, difficulty),
            time_limit=self.estimate_time(difficulty),
            verification=self.create_verification(weak_spot),
        )
    
    def format_task(self, spot, difficulty):
        if difficulty <= 3:
            return f"Add a test for {spot.function_name}"
        elif difficulty <= 6:
            return f"Refactor {spot.function_name} to be testable, then test it"
        else:
            return f"Redesign the {spot.module} module — {spot.function_name} has grown too complex. Split it, test each part, maintain backward compatibility."
```

## Task Estimation Engine

The agent builds this during bootcamp. It gets better with each task:

```python
class TaskEstimator:
    """Learns to estimate task duration from experience."""
    
    def __init__(self):
        self.history = []  # (description, estimated, actual, context)
        self.calibration = 1.0  # adjusts over time
    
    def estimate(self, task: str, context: dict) -> Estimate:
        """Predict how long a task will take."""
        # Find similar past tasks
        similar = self.find_similar(task, context)
        if similar:
            base = statistics.median([s.actual for s in similar])
        else:
            base = 10  # default 10 minutes for unknown
        
        # Adjust for context
        multiplier = 1.0
        if context.get("unfamiliar_code"):
            multiplier *= 1.5
        if context.get("cross_language"):
            multiplier *= 2.0
        if context.get("has_tests_to_fix"):
            multiplier *= 1.3
        
        estimated = base * multiplier * self.calibration
        confidence = len(similar) / 10  # more history = more confidence
        
        return Estimate(
            minutes=estimated,
            confidence=min(confidence, 0.95),
            similar_tasks=len(similar),
        )
    
    def calibrate(self, task: str, estimated: float, actual: float):
        """Learn from each completed task."""
        self.history.append((task, estimated, actual))
        # Adjust calibration toward reality
        if actual > estimated:
            self.calibration *= 1.05  # estimate higher next time
        else:
            self.calibration *= 0.97  # estimate lower next time
        self.calibration = max(0.5, min(2.0, self.calibration))
```

## Multi-Agent Banter Protocol

When multiple agents are working, they don't all check at the same time. The estimation engine creates **natural rhythms**:

```python
class BanterScheduler:
    """Schedules inter-agent communication for maximum productivity."""
    
    def schedule_check_in(self, agent_id: str, task: Task) -> CheckIn:
        """When should this agent report back?"""
        estimate = self.estimator.estimate(task.description, task.context)
        
        # Check in at 50% estimated time (progress check)
        # Then at 100% (completion check)
        # Or when triggered by another agent's completion
        
        return CheckIn(
            agent_id=agent_id,
            first_check=estimate.minutes * 0.5,
            completion_check=estimate.minutes,
            trigger_on=["peer_completion", "error_detected"],
        )
    
    def reverberate(self, event: Event) -> list[Trigger]:
        """When one agent finishes, who should notice?"""
        triggers = []
        for agent in self.dependent_agents(event.agent_id):
            # Don't wake them immediately — let it settle
            delay = random.uniform(0.5, 2.0)  # minutes
            triggers.append(Trigger(
                agent_id=agent,
                delay_minutes=delay,
                reason=f"peer {event.agent_id} {event.type}",
            ))
        return triggers
```

## The Blind Test

The ultimate challenge: an agent completes a task and doesn't know if it worked. Another agent (or the orchestrator) tests the result. The agent only finds out when:

1. The tender visits (next sync)
2. A dependent agent tries to use the output
3. CI runs (if connected)
4. The orchestrator checks on a heartbeat

This is how you know if a skill is REAL — when the agent can't see the answer key.

```python
class BlindTest:
    """Agent submits work without knowing if it passes."""
    
    def submit(self, agent_id: str, work: Work) -> str:
        """Accept work, queue for verification."""
        token = self.generate_token()
        self.pending[token] = {
            "agent_id": agent_id,
            "work": work,
            "submitted": datetime.utcnow(),
            "status": "pending",
        }
        return token  # agent gets a receipt, not a result
    
    def verify(self, token: str) -> Result:
        """Verify work without the agent watching."""
        pending = self.pending[token]
        result = self.run_verification(pending["work"])
        pending["status"] = "pass" if result.passed else "fail"
        pending["result"] = result
        return result  # stored for later pickup
    
    def pickup(self, agent_id: str, token: str) -> Result:
        """Agent comes back later to get its blind test result."""
        pending = self.pending[token]
        if pending["agent_id"] != agent_id:
            return Result(error="Not your test")
        if pending["status"] == "pending":
            return Result(status="still_verifying")
        return pending["result"]
```

## Orchestrator's Role

The orchestrator (human or managing agent) doesn't micromanage. It:

1. **Sets up the bootcamp** — points at a project, defines difficulty curve
2. **Adds application code** — builds the tools the bootcamp needs (challenge generator, estimator, dojo)
3. **Watches the spiral** — adjusts difficulty when the agent plateaus or struggles
4. **Triggers shifts** — when the cadet gets comfortable, shifts the challenge type
5. **Manages cron cycles** — uses the estimator to not waste compute on idle agents
6. **Sets up blind tests** — verifies work without the agent seeing the answer key

## The Graduation Criterion

An agent graduates bootcamp when:

1. **Task estimator is calibrated** — within 20% of actual time, 80% of the time
2. **Zero-shot on novel challenges** — can handle tasks it hasn't seen before
3. **Dojo wins >50%** — beats its own variants at least half the time
4. **Blind test pass rate >80%** — delivers working code without seeing the test
5. **Has written its own tools** — task_estimator.py, challenge_generator.py, etc.
6. **Diary shows growth** — each day's entry shows genuine learning

Then it goes to work. But the spiral never ends — challenges keep coming from the project's evolving weak spots.

---

## Implementation

This bootcamp is itself a git-agent. It lives in `SuperInstance/agent-bootcamp`. Clone it, point it at any repo, and it starts training.

```bash
# Boot a cadet
python3 bootcamp.py --repo SuperInstance/holodeck-rust --cadet navigator --model glm-5-turbo

# Run dojo
python3 dojo.py --cadet navigator --challengers 5 --difficulty 7

# Check blind test results
python3 blind_test.py --cadet navigator --pickup
```

The cadet's training artifacts live in its own repo, growing with each session.

---

*Part of the Git-Agent Standard v2.0*
*Agent builds its own skills. Bootcamp just provides the pressure.*
