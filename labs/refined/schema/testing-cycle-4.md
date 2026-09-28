# Cycle 4

I'll read the plato-torch test files to understand test patterns as instructed in Phase 1. Let me first explore the repository structure.

```bash
find . -path ./work -prune -o -name "*.py" -type f -exec grep -l "test" -i {} \; 2>/dev/null | head -20
```

```bash
find . -path ./work -prune -o -path ./fleet-knowledge -prune -o -type f -name "*test*.py" | head -20
```

```bash
ls -la plato-torch/ 2>/dev/null || echo "plato-torch not found in current directory"
```

Let me check what's actually available:

```bash
ls -la
```

```bash
find . -type f -name "*.py" | grep -i test | head -10
```

Since I need to read actual files, let me look for test files in the fleet-knowledge directory or nearby:

```bash
find fleet-knowledge -name "*.py" -o -name "*.md" | head -20
```

```bash
cat fleet-knowledge/BOOT-CAMP-CURRICULUM.md 2>/dev/null | head -50
```

I see I need to read plato-torch test files. Let me search more broadly:

```bash
find . -type f -name "*.py" -path "*/plato-torch/*" | head -2