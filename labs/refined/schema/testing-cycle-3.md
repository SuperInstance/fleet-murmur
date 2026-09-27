# Cycle 3

I'll examine the DeadbandRoom preset and write edge-case tests.

```bash
find . -path ./work -prune -o -name "*.py" -type f -exec grep -l "DeadbandRoom" {} \; 2>/dev/null | head -10
```

```bash
find . -path ./work -prune -o -name "*.py" -type f -exec grep -l "deadband" -i {} \; 2>/dev/null | head -10
```

```bash
find . -path ./work -prune -o -name "*.py" -type f -exec grep -B2 -A10 "class DeadbandRoom" {} \; 2>/dev/null
```

Let me check the plato-torch directory structure:

```bash
ls -la plato-torch/
```

```bash
find plato-torch -name "*.py" -type f | xargs grep -l "DeadbandRoom" 2>/dev/null
```

```bash
find plato-torch -name "*.py" -type f | xargs grep -l "deadband" -i 2>/dev/null
```

Let me look for test files:

```bash
find . -path ./work -prune -o -name "*test*.py" -type f | xargs grep -l "deadband" -i 2>/dev/null
```

Found it! Let me examine the DeadbandRoom implementation:

```bash
find . -path ./work -prune -o -name "*.py" -type f -exec grep -B5 -A20 "class DeadbandRoom"