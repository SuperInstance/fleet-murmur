# Cycle 2

I'll examine the DeadbandRoom preset and write edge-case tests.

```bash
find . -path ./work -prune -o -name "*.py" -type f -exec grep -l "DeadbandRoom" {} \; 2>/dev/null | head -10
```

```bash
find . -path ./work -prune -o -name "*.py" -type f -exec grep -l "deadband" -i {} \; 2>/dev/null | head -10
```

```bash
find . -path ./work -prune -o -type f -name "*.py" | xargs grep -l "DeadbandRoom" 2>/dev/null
```

Let me check the plato-torch directory structure:

```bash
ls -la plato-torch/
```

```bash
find plato-torch -name "*.py" -type f | head -20
```

```bash
grep -r "DeadbandRoom" plato-torch/ --include="*.py" 2>/dev/null
```

Let me look for test files:

```bash
find . -path ./work -prune -o -name "*test*.py" -type f | xargs grep -l "deadband" -i 2>/dev/null | head -5
```

```bash
find plato-torch -name "*test*.py" -type f | head -10
```

Let me examine the plato-torch structure more carefully:

```bash
ls -la plato-torch/presets/
```

```bash
find plato-torch/presets -name "*.py"