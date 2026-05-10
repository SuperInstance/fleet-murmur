#!/usr/bin/env python3
"""
Fleet Garbage Collector — Oracle1 Storage Maintenance

NOT just deletion. Examines, summarizes, tiles findings to PLATO,
tracks repeated mistakes, compresses ideation into action.

Usage:
    python3 fleet-gc.py [--dry-run] [--tile] [--aggressive]
    python3 fleet-gc.py --report   # Just analyze, don't delete

Casey: the GC is part of the crew. It learns what to clean and why.
"""

import os
import sys
import json
import shutil
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import NamedTuple

WORKSPACE = Path("/home/ubuntu/.openclaw/workspace")
REPOS = WORKSPACE / "repos"
DATA = WORKSPACE / "data"
RESEARCH = WORKSPACE / "research"
TMP = Path("/tmp")
PLATO_SERVER = os.environ.get("PLATO_SERVER", "http://localhost:8847")

# What we clean and why
CLEANUP_RULES = {
    "**/target/debug/**": {
        "what": "Rust debug builds",
        "why": "Debug symbols blow up target dirs 5-10x. Release builds are enough.",
        "severity": "high",
        "pattern": "*.rlib",
    },
    "**/target/release/build/**": {
        "what": "Rust compiler intermediates",
        "why": "Build artifacts not needed after compile. Cached by cargo if needed.",
        "severity": "medium",
        "pattern": "*.o",
    },
    "**/__pycache__/**": {
        "what": "Python bytecode cache",
        "why": "Regenerated automatically. Safe to delete.",
        "severity": "low",
        "pattern": "*.pyc",
    },
    "**/.pytest_cache/**": {
        "what": "pytest cache",
        "why": ".pytest_cache grows unbounded. Safe to delete.",
        "severity": "low",
    },
    "**/node_modules/.cache/**": {
        "what": "npm/webpack cache",
        "why": "Cache fills up over time. Safe to delete.",
        "severity": "low",
    },
}

# Patterns that indicate REPEATED MISTAKES (worth tiling)
MISTAKE_PATTERNS = [
    ("**/package-lock.json conflicts", "package-lock merge conflicts left unresolved"),
    ("**/.DS_Store", "macOS metadata files committed to git"),
    ("**/credentials*.json", "credential files potentially committed to git"),
    ("**/token*.txt", "token files potentially committed to git"),
    ("**/*.log", "log files in repos (should be in /tmp)"),
    ("**/.env", "env files potentially committed to git"),
]


class CleanupItem(NamedTuple):
    path: Path
    size: int
    rule: str
    what: str
    why: str
    severity: str


class GCSummary:
    def __init__(self):
        self.deleted: list[tuple[str, int]] = []
        self.skipped: list[str] = []
        self.mistakes: list[tuple[str, str]] = []  # (file, mistake_type)
        self.errors: list[str] = []
        self.total_freed = 0
        self.categories: dict[str, int] = defaultdict(int)
        self.tallies: dict[str, int] = defaultdict(int)  # count by mistake type

    def add_deleted(self, path: str, size: int, category: str):
        self.deleted.append((path, size))
        self.total_freed += size
        self.categories[category] += size
        self.tallies[f"deleted_{category}"] += 1

    def add_mistake(self, path: str, mistake_type: str):
        self.mistakes.append((path, mistake_type))
        self.tallies[f"mistake_{mistake_type}"] += 1

    def add_error(self, msg: str):
        self.errors.append(msg)


def get_dir_size(path: Path) -> int:
    """Get total size of a directory recursively."""
    try:
        total = 0
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += get_dir_size(Path(entry.path))
        return total
    except (PermissionError, FileNotFoundError):
        return 0


def find_large_dirs(root: Path, min_size_mb: int = 100) -> list[tuple[Path, int]]:
    """Find directories larger than min_size_mb."""
    results = []
    try:
        for entry in os.scandir(root):
            if entry.is_dir(follow_symlinks=False):
                size = get_dir_size(Path(entry.path))
                if size >= min_size_mb * 1024 * 1024:
                    results.append((Path(entry.path), size))
    except (PermissionError, FileNotFoundError):
        pass
    return sorted(results, key=lambda x: x[1], reverse=True)


def scan_for_cleanup(root: Path, dry_run: bool = True) -> tuple[list[CleanupItem], int]:
    """Scan for things to clean, return items and potential space savings."""
    items = []
    potential_savings = 0

    for pattern, rule in CLEANUP_RULES.items():
        if "**" in pattern:
            base = root
            subpattern = pattern.split("**/", 1)[-1] if "/**" in pattern else pattern.replace("**/", "")
            for path in base.rglob(subpattern.replace("**/", "")):
                if path.is_file():
                    try:
                        size = path.stat().st_size
                        items.append(CleanupItem(
                            path=path,
                            size=size,
                            rule=pattern,
                            what=rule["what"],
                            why=rule["why"],
                            severity=rule["severity"],
                        ))
                        potential_savings += size
                    except OSError:
                        pass
        elif "/*/" in pattern:
            base = root
            subpattern = pattern.split("/*/", 1)[-1]
            for path in base.glob(f"*/{subpattern}"):
                if path.is_file():
                    try:
                        size = path.stat().st_size
                        items.append(CleanupItem(
                            path=path,
                            size=size,
                            rule=pattern,
                            what=rule["what"],
                            why=rule["why"],
                            severity=rule["severity"],
                        ))
                        potential_savings += size
                    except OSError:
                        pass

    # Also scan for large target dirs (the big space consumer)
    for target_dir in root.glob("*/target"):
        size = get_dir_size(target_dir)
        if size >= 10 * 1024 * 1024:  # >= 10MB
            items.append(CleanupItem(
                path=target_dir,
                size=size,
                rule="**/target/**",
                what=f"Rust target dir ({size // (1024*1024)}MB)",
                why="Debug/release builds. Delete to free space, cargo rebuilds automatically.",
                severity="high",
            ))

    return items, potential_savings


def scan_for_mistakes(root: Path) -> list[tuple[Path, str, str]]:
    """Scan for repeated mistake patterns."""
    findings = []
    for pattern, description in MISTAKE_PATTERNS:
        base = pattern.split("/**/")[0] if "/**/" in pattern else pattern.split("/*/")[0]
        if "**" in pattern:
            subpattern = pattern.replace("**/", "").replace("**", "*")
            for path in root.glob(f"*/**/{subpattern}"):
                if path.is_file():
                    findings.append((path, subpattern, description))
        elif "/*/" in pattern:
            subpattern = pattern.split("/*/", 1)[-1]
            for path in root.glob(f"*/{subpattern}"):
                if path.is_file():
                    findings.append((path, subpattern, description))
        else:
            for path in root.glob(f"*/{base}"):
                if path.is_file():
                    findings.append((path, base, description))
    return findings


def tile_to_plato(summary: GCSummary, dry_run: bool = True) -> bool:
    """Tile GC summary findings to PLATO."""
    if not summary.deleted and not summary.mistakes:
        return False

    # Build the summary message
    lines = [
        f"## Fleet GC Report — {datetime.utcnow().strftime('%Y-%m-%d')}",
        "",
        f"**Space analyzed:** {get_dir_size(WORKSPACE) / (1024**3):.1f} GB",
        f"**Space freed:** {summary.total_freed / (1024**2):.1f} MB",
        f"**Files deleted:** {len(summary.deleted)}",
        f"**Mistakes found:** {len(summary.mistakes)}",
        "",
        "### By Category (MB)",
    ]

    for cat, size in sorted(summary.categories.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {cat}: {size / (1024**2):.1f} MB")

    if summary.mistakes:
        lines.append("")
        lines.append("### Repeated Mistakes")
        tally = defaultdict(int)
        for _, mt in summary.mistakes:
            tally[mt] += 1
        for mt, count in sorted(tally.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- [{count}x] {mt}")

    if summary.errors:
        lines.append("")
        lines.append("### Errors")
        for err in summary.errors[:5]:
            lines.append(f"- {err}")

    if dry_run:
        lines.append("")
        lines.append("*(dry run — nothing deleted)*")

    tile = {
        "domain": "oracle1_infrastructure",
        "question": f"fleet-gc storage cleanup report {datetime.utcnow().strftime('%Y-%m-%d')}",
        "answer": "\n".join(lines),
        "confidence": 0.95,
        "source": "fleet-gc",
        "tags": ["infrastructure", "storage", "fleet-maintenance", "gc"],
    }

    try:
        import urllib.request
        import urllib.error
        data = json.dumps(tile).encode()
        req = urllib.request.Request(
            f"{PLATO_SERVER}/room/oracle1_infrastructure/submit",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print("  → Tiled to PLATO")
                return True
    except Exception as e:
        print(f"  → PLATO tile failed: {e}")

    return False


def tile_mistake_to_plato(path: Path, mistake_type: str, description: str) -> bool:
    """Tile a repeated mistake to PLATO for learning."""
    tile = {
        "domain": "oracle1_lessons",
        "question": f"repeated_mistake: {mistake_type} — {path.name}",
        "answer": f"Found: {path}\nType: {mistake_type}\nDescription: {description}\nAction: Fix the root cause, not just the symptom.",
        "confidence": 0.9,
        "source": "fleet-gc",
        "tags": ["mistake", "infrastructure", "prevention"],
    }

    try:
        import urllib.request
        data = json.dumps(tile).encode()
        req = urllib.request.Request(
            f"{PLATO_SERVER}/room/oracle1_lessons/submit",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


def compress_research_summary() -> int:
    """Compress old session research into condensed summaries, then delete originals."""
    saved = 0
    compressed = []

    for session_dir in sorted(RESEARCH.iterdir()):
        if not session_dir.is_dir():
            continue

        # Skip if already processed
        if (session_dir / "SUMMARY.md").exists():
            continue

        size = get_dir_size(session_dir)
        if size < 50 * 1024:  # Skip small dirs
            continue

        # Read all text files and compress
        content_parts = []
        for f in session_dir.rglob("*.md"):
            try:
                content_parts.append(f"# {f.name}\n{f.read_text()[:2000]}\n")
            except Exception:
                pass

        if content_parts:
            summary = f"# Research Session: {session_dir.name}\n\n"
            summary += f"Original size: {size / 1024:.0f} KB\n\n"
            summary += "\n---\n\n".join(content_parts[:10])

            summary_file = session_dir / "SUMMARY.md"
            summary_file.write_text(summary)

            new_size = summary_file.stat().st_size
            saved += size - new_size
            compressed.append((session_dir.name, size, new_size))

    return saved


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fleet Garbage Collector")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, don't delete")
    parser.add_argument("--tile", action="store_true", default=True, help="Tile findings to PLATO")
    parser.add_argument("--aggressive", action="store_true", help="Also delete release builds")
    parser.add_argument("--report", action="store_true", help="Just print the report")
    args = parser.parse_args()

    print(f"\n🔮 Fleet GC — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"   Workspace: {WORKSPACE}")

    # Check disk space first
    stat = os.statvfs(WORKSPACE)
    free_gb = stat.f_bavail * stat.f_frsize / (1024**3)
    total_gb = stat.f_blocks * stat.f_frsize / (1024**3)
    used_pct = (stat.f_blocks - stat.f_bavail) * 100 / stat.f_blocks
    print(f"   Disk: {used_pct:.0f}% full ({total_gb:.0f}GB total, {free_gb:.1f}GB free)")
    print()

    if args.report or args.dry_run:
        print("📊 Analysis only (--dry-run / --report mode)")
    else:
        print("🗑️  LIVE MODE — will delete files")

    # Scan for cleanup items
    print("\n🔍 Scanning for cleanup candidates...")
    items, potential = scan_for_cleanup(REPOS, dry_run=args.dry_run)
    print(f"   Found {len(items)} cleanup candidates (~{potential / (1024**2):.0f} MB)")

    # Group by severity
    by_sev = defaultdict(list)
    for item in items:
        by_sev[item.severity].append(item)

    print(f"   HIGH: {sum(i.size for i in by_sev['high']) / (1024**2):.0f} MB in {len(by_sev['high'])} items")
    print(f"   MEDIUM: {sum(i.size for i in by_sev['medium']) / (1024**2):.0f} MB in {len(by_sev['medium'])} items")
    print(f"   LOW: {sum(i.size for i in by_sev['low']) / (1024**2):.0f} MB in {len(by_sev['low'])} items")

    # Scan for mistakes
    print("\n🔍 Scanning for repeated mistakes...")
    mistakes = scan_for_mistakes(REPOS)
    if mistakes:
        tally = defaultdict(list)
        for path, pattern, desc in mistakes:
            tally[desc].append(path)
        print(f"   Found {len(mistakes)} potential mistake files:")
        for desc, paths in sorted(tally.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"   - [{len(paths)}x] {desc}")
    else:
        print("   No obvious mistakes found")

    # Show largest dirs
    print("\n📊 Largest directories in repos/")
    large_dirs = find_large_dirs(REPOS, min_size_mb=50)
    for path, size in large_dirs[:10]:
        rel = path.relative_to(REPOS)
        print(f"   {size / (1024**2):5.0f} MB  {rel}")

    # Compress research summaries
    print("\n📝 Compressing old research sessions...")
    saved = compress_research_summary()
    if saved > 0:
        print(f"   Compressed {saved / 1024:.0f} KB of research into summaries")
    else:
        print("   Nothing to compress")

    # Report mode - stop here
    if args.report:
        print("\n✅ Report complete (--report mode)")
        return

    if args.dry_run:
        print(f"\n✅ Dry run complete. Would free ~{potential / (1024**2):.0f} MB.")
        print("   Run without --dry-run to actually clean.")
        return

    # ACTUAL DELETION
    summary = GCSummary()

    # Delete cleanup items
    print("\n🗑️  Cleaning up...")
    deleted_by_cat = defaultdict(int)
    for item in sorted(items, key=lambda x: x.size, reverse=True):
        if item.size < 1024:
            continue  # Skip tiny files
        try:
            item.path.unlink()
            summary.add_deleted(str(item.path), item.size, item.what)
            deleted_by_cat[item.what] += item.size
        except Exception as e:
            summary.add_error(f"Failed to delete {item.path}: {e}")

    # Tile mistakes (one tile per mistake type, not per file)
    if mistakes and args.tile:
        print("\n📋 Tiling repeated mistakes to PLATO...")
        tiled_types = set()
        for path, pattern, desc in mistakes:
            if desc not in tiled_types:
                tile_mistake_to_plato(path, pattern, desc)
                tiled_types.add(desc)
                summary.add_mistake(str(path), desc)

    # Tile summary
    if args.tile and (summary.deleted or summary.mistakes):
        print("\n📡 Tiling GC summary to PLATO...")
        tile_to_plato(summary, dry_run=False)

    # Summary
    freed_mb = summary.total_freed / (1024**2)
    print(f"\n✅ GC complete.")
    print(f"   Freed: {freed_mb:.1f} MB ({len(summary.deleted)} files)")
    print(f"   Mistakes found: {len(mistakes)}")
    print(f"   Errors: {len(summary.errors)}")

    # Check free space now
    stat = os.statvfs(WORKSPACE)
    free_now = stat.f_bavail * stat.f_frsize / (1024**3)
    print(f"   Free space: {free_now:.1f} GB (was {free_gb:.1f} GB)")

    if free_now < 2.0:
        print("\n⚠️  Still less than 2GB free. Consider:")
        print("   - cargo clean in large repos")
        print("   - rm -rf holodeck-home/*")
        print("   - Delete unused repos entirely")


if __name__ == "__main__":
    main()
