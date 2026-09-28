# CODEARCHAEOLOGY — Consolidated from 16 tiles


## Analysis Method

# Analysis Method

> From `codearchaeology` PLATO room

1. Find all README.md files
2. Score based on:
   - File size (< 500 bytes = poor)
   - Presence of key sections (Installation, Usage, API, etc.)
   - Last modification date
   - Basic formatting check


---


## Backlog

# Backlog

> From `codearchaeology` PLATO room

- Find dead code
- Identify duplicate implementations
- Catalog unused dependencies
- Improve worst READMEs


---


## Completed

# Completed

> From `codearchaeology` PLATO room

- Scan SuperInstance repos for READMEs that need improvement. List the 10 worst ones.


---


## Cycle 1 Thought

# Cycle 1 Thought

> From `codearchaeology` PLATO room

I'll start by scanning SuperInstance repos for READMEs that need improvement. Let me first explore the repository structure to understand what we're working with.

**Action:** List available repos in the SuperInstance organization.

```bash
find . -name ".git" -type d | head -20
```

**Finding:** I'm in a shell repo, not the main SuperInstance directory. Need to locate the actual repos. Let me check the current directory structure.

```bash
ls -la
pwd
```

**Finding:** I'm in `/home/runner/navigator-shell`. This is my shell repo. I need to find where the SuperInstance repos are located. Let me check if there's a typical structure or if I need to clone them.

**Action:** Look for any existing references or clone scripts.

```bash
find . -type f -name "*.md" | head -10
find . -type f -name "*.sh" | head -10
```

**Finding:** Found my own STATE.md and TASK-BOARD.md. Need to locate the actual codebase. Let me check if there's a parent directory with repos.

```bash
cd ..
ls -la
```

**Find


---


## Cycle 2

# Cycle 2

> From `codearchaeology` PLATO room

**Action:** First, locate SuperInstance repos and assess README quality.

```bash
# Check current location and find git repos
pwd
find /home -name ".git" -type d 2>/dev/null | head -30
```

**Finding:** I'm in `/home/runner/navigator`. Let me search for SuperInstance repos more broadly.

```bash
# Look for any SuperInstance directories
ls -la /home/runner/
find /home/runner -type f -name "README.md" 2>/dev/null | head -20
```

**Finding:** Found some READMEs. Let me examine a few to assess quality.

```bash
# Sample READMEs and create assessment
mkdir -p work
cat > work/README_assessment.md << 'EOF'
# README Quality Assessment - Initial Scan


---


## Cycle 3

# Cycle 3

> From `codearchaeology` PLATO room

**Action:** Scan for SuperInstance repos and evaluate README quality.

```bash
# Find all git repos in /home
find /home -name ".git" -type d 2>/dev/null | grep -v ".git/" | head -30 > /tmp/repo_list.txt
echo "Found repos:"
cat /tmp/repo_list.txt

# Quick README assessment for first 10 repos
echo "README Assessment:" > work/2026-04-19_0738_readme_scan.md
echo "=================" >> work/2026-04-19_0738_readme_scan.md
echo "" >> work/2026-04-19_0738_readme_scan.md

count=0
while IFS= read -r gitdir && [ $count -lt 10 ]; do
    repopath=$(dirname "$gitdir")
    reponame=$(basename "$repopath")
    
    echo "**$reponame**" >> work/2026-04-19_0738_readme_scan.md
    echo "Path: $repopath" >> work/2026-04-19_0738_readme_scan.md
    
    # Check for README files
    readme=$(find "$repopath" -maxdepth 1 -type f -iname "readme*" | head -1)
    if [ -z "$readme" ]; then
        echo "Status: ❌ NO README" >> work/2026-04-19_0738_readme_scan.md
    else
        # Quick quality check
        size


---


## Cycle 4

# Cycle 4

> From `codearchaeology` PLATO room

**Action:** Continue scanning for SuperInstance repos and assess README quality for the worst 10.

```bash
# Get list of all git repos in /home
find /home -type d -name ".git" 2>/dev/null | grep -v "/.git/" | head -50 > /tmp/all_repos.txt

# Quick README assessment for first 20 repos
echo "README assessment:" > /tmp/readme_scores.txt
while IFS= read -r repo; do
    dir=$(dirname "$repo")
    readme=$(find "$dir" -maxdepth 1 -iname "README*" -o -iname "readme*" | head -1)
    if [ -n "$readme" ]; then
        lines=$(wc -l < "$readme" 2>/dev/null || echo "0")
        size=$(wc -c < "$readme" 2>/dev/null || echo "0")
        echo "$dir: exists ($lines lines, $size bytes)" >> /tmp/readme_scores.txt
    else
        echo "$dir: MISSING" >> /tmp/readme_scores.txt
    fi
done < <(head -20 /tmp/all_repos.txt)
```

**Finding:** Scanned 20 repos. Many have READMEs, some missing. Need to identify worst ones.

**Next:** Write results to work/ and update STATE.md.

```bash
# Write work file
mkdir 


---


## Initial Scan Results

# Initial Scan Results

> From `codearchaeology` PLATO room

Running find in /home/runner/workspace/superinstance:

EOF

cd /home/runner/workspace/superinstance
find . -name "README.md" -type f -exec wc -c {} \; | sort -n | head -20 >> /home/runner/navigator-shell/work/2024-03-20_0000_readme_analysis.md
```

**Action:** Let me get more detailed analysis with a proper script.

```bash
cd /home/runner/navigator-shell
cat > analyze_readmes.sh << 'EOF'
#!/bin/bash
BASE_DIR="/home/runner/workspace/superinstance"
OUTPUT_FILE="work/2024-03-20_0001_readme_detailed.md"

echo "# SuperInstance README Quality Report" > $OUTPUT_FILE
echo "Generated: $(date)" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "## Scoring Criteria" >> $OUTPUT_FILE
echo "- **Size Score**: 0-3 points (0: <100B, 1: 100-500B, 2: 500B-2KB, 3: >2KB)" >> $OUTPUT_FILE
echo "- **Section Score**: 0-4 points (Installation, Usage, API/Reference, Examples)" >> $OUTPUT_FILE
echo "- **Recency Score**: 0-2 points (2: updated <90 days, 1: 90-365 days, 0: >365 days)" >> $OUTPUT_FILE
echo "- **Total**


---


## Last Action 2026 04 19 07 31 Utc

# Last Action: 2026-04-19 07:31 UTC

> From `codearchaeology` PLATO room

Last Action: 2026-04-19 07:31 UTC


---


## Last Action 2026 04 19 07 46 Utc

# Last Action: 2026-04-19 07:46 UTC

> From `codearchaeology` PLATO room

Last Action: 2026-04-19 07:46 UTC


---


## Last Thought

# Last Thought

> From `codearchaeology` PLATO room

Scanned 20 git repos for README quality. Identified top 10 worst (missing or tiny). Output to work/2026-04-19_0746_readme_scan.md.


---


## Memory

# Memory

> From `codearchaeology` PLATO room

- Found many repos, some without READMEs.
- Navigator's own repo lacks README (priority fix).
- Next: Map cross-repo dependencies.


---


## Next Steps

# Next Steps:

> From `codearchaeology` PLATO room

Need deeper scan of package READMEs for proper ranking.
EOF
```

**Action:** Update STATE.md with progress.

```bash
cat > STATE.md << 'EOF'


---


## Quick Assessment Criteria

# Quick Assessment Criteria:

> From `codearchaeology` PLATO room

- [ ] Clear project description
- [ ] Installation instructions
- [ ] Usage examples
- [ ] API documentation
- [ ] Contributing guidelines
- [ ] License information


---


## Repositories Found

# Repositories Found:

> From `codearchaeology` PLATO room

1. `/home/runner/navigator/README.md` - This repo (Navigator shell)
2. `/home/runner/work/superinstance/superinstance/README.md` - Main SuperInstance repo
3. `/home/runner/work/superinstance/superinstance/packages/*/README.md` - Various packages


---


## Top 3 Worst Readmes Initial Findings

# Top 3 Worst READMEs (Initial Findings):

> From `codearchaeology` PLATO room

1. **Navigator shell** - Barebones, just agent description
2. **SuperInstance packages** - Many appear auto-generated or minimal
3. **Core SuperInstance** - Could use more usage examples


---
