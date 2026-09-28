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
