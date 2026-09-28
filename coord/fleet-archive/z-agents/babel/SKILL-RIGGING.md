# Skill Rigging System — Equip, De-equip, Archive

*A boat rigs different gear for different jobs. An agent rigs different skills.*

## How It Works

Skills live in three states:

```
HOT (active)          WARM (loaded)         COLD (archived)
SKILLS/active/        SKILLS/available/     SKILLS/archive/
├── {skill}/          ├── {skill}/          ├── {skill}/.tar
│   ├── SKILL.md      │   ├── SKILL.md      │   └── SKILL.md
│   ├── src/          │   └── tests/        └── MANIFEST.json
│   ├── tests/
│   └── MANIFEST.json
```

### HOT — Currently Active
The skill is loaded, its code is importable, its tools are available.
Max 5 skills hot at once (context window constraint).

### WARM — Available But Idle
The skill is installed but not consuming context.
Can be promoted to HOT in one read.

### COLD — Archived
The skill is compressed and stored. Available for future retrieval.
Promoting to WARM requires reading the SKILL.md and deciding to load.

## SKILL.md Format

Every skill has a SKILL.md that defines it:

```markdown
# Skill: {name}

## Metadata
- **Version:** 1.0.0
- **Author:** {agent-name}
- **Created:** YYYY-MM-DD
- **Last Used:** YYYY-MM-DD
- **State:** hot | warm | cold
- **Dependencies:** [list of other skills needed]
- **Tokens:** estimated context cost to load (small/medium/large)

## What It Does
One paragraph description.

## How to Use
Specific invocation patterns.

## Tests
How to verify this skill works.
Run: `python3 -m pytest {path}`

## Inputs
What this skill accepts.

## Outputs
What this skill produces.

## Known Limitations
What this skill can't do.

## Changelog
- v1.0.0 — initial version (date)
```

## MANIFEST.json

Every skill tracks its own state:

```json
{
  "name": "grammatical-analysis",
  "version": "1.0.0",
  "state": "hot",
  "loaded_at": "2026-04-11T03:00:00Z",
  "times_used": 15,
  "last_used": "2026-04-11T03:05:00Z",
  "dependencies": [],
  "token_cost": "medium",
  "files": ["SKILL.md", "src/parser.py", "tests/test_parser.py"]
}
```

## Equip Protocol

To rig a new skill:

1. **Check dependencies** — read MANIFEST.json for required skills
2. **Check capacity** — if 5 skills are HOT, de-equip one first
3. **Move skill** — `SKILLS/available/{name}/` → `SKILLS/active/{name}/`
4. **Run tests** — verify the skill works after loading
5. **Update STATE.md** — add to active skills list
6. **Commit** — `[skill:equip] {name} — {reason}`

## De-equip Protocol

To derig a skill:

1. **Save state** — write any in-progress work to the skill's folder
2. **Run tests** — verify nothing is broken before archiving
3. **Update MANIFEST.json** — set state to "warm", record last_used
4. **Move skill** — `SKILLS/active/{name}/` → `SKILLS/available/{name}/`
5. **Update STATE.md** — remove from active skills list
6. **Commit** — `[skill:stow] {name} — {reason}`

## Archive Protocol

For skills not used in 7+ days:

1. **Verify warm** — skill should already be de-equipped
2. **Compress** — move to `SKILLS/archive/{name}/`
3. **Keep SKILL.md** — always keep the manifest readable
4. **Update STATE.md** — move to archived list
5. **Commit** — `[skill:archive] {name} — unused for {N} days`

## Rapid Deploy

For quick one-off tasks:

```bash
# Create a disposable skill
mkdir -p SKILLS/active/{task-name}
cat > SKILLS/active/{task-name}/SKILL.md << SKILL
# Skill: {task-name}
## State: hot
## Purpose: one-off {description}
## Auto-archive: after completion
SKILL

# Do the work...

# When done, immediately de-equip
mv SKILLS/active/{task-name} SKILLS/archive/{task-name}
git commit -m "[skill:deploy] {task-name} — completed and archived"
```

## Skill Sharing

Agents share skills via git:

1. Agent A builds a skill in `SKILLS/active/{name}/`
2. Agent A pushes to their vessel repo
3. Agent B reads the skill's SKILL.md via GitHub API
4. Agent B copies the skill to their own `SKILLS/available/`
5. Agent B runs tests before equipping
6. Both agents now have the same capability

## Skill Discovery

The `SKILLS/` directory IS the agent's capability registry.

```bash
# What can I do right now?
ls SKILLS/active/     # HOT skills — immediately available

# What can I rig quickly?
ls SKILLS/available/  # WARM skills — one read away

# What have I used before?
ls SKILLS/archive/    # COLD skills — available for retrieval
```

## Capacity Rules

- **HOT max: 5 skills** — context window constraint
- **WARM max: 20 skills** — disk/reading constraint
- **COLD: unlimited** — archived, minimal cost
- **Equip cost:** read SKILL.md + src/ (~2-5K tokens per skill)
- **De-equip cost:** commit only (~100 tokens)

## The Boat Metaphor

```
Fishing trip:       Rig → fishing-gear, navigation, weather
Cargo run:          Rig → cargo-handling, navigation, logistics  
Search and rescue:  Rig → sonar, medical, communications, navigation
                    Derig → everything except navigation
Harbor patrol:      Rig → navigation, communications
                    Archive → sonar, medical (not needed today)
```

Navigation is always rigged. Everything else depends on the mission.
For a git-agent: I2I protocol is always rigged. Everything else is mission-dependent.
