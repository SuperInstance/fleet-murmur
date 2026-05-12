# 🌐 Cross-Pollination Protocol

> *Every repo in the fleet should know about its neighbors. Cross-pollination ensures no repo is an island.*

## Meta-Headers

Each repo's README should include `<!-- x-ref -->` comments listing related repos:

```markdown
<!-- x-ref fleet-coordinate: ZHC consensus + emergence -->
<!-- x-ref fleet-murmur: workshop workspace, heartbeat tasks -->
```

## Audit

Run `scripts/dependency-scanner.py` weekly to:
1. Scan all SuperInstance repos for cross-references
2. Generate CROSS-REFERENCES.md
3. Report orphan repos (no refs to or from any other fleet repo)

## Rules

1. Every repo should reference at least 2 other fleet repos
2. Key architecture docs (flux-mesh, keel) should reference downstream repos
3. New repos get meta-headers within 24h of creation
4. The scanner output is checked into `CROSS-REFERENCES.md`
