#!/usr/bin/env python3
"""
SuperInstance Cross-Reference Dependency Scanner

Scans all public repos for cross-references to other repos in the organization.
Generates:
1. CROSS-REFERENCES.md — full cross-reference index
2. Missing backlink report

Usage:
    GITHUB_TOKEN=ghp_xxx python3 scripts/dependency-scanner.py
    # or use gh auth
    python3 scripts/dependency-scanner.py
"""

import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Set, Tuple

ORG = "SuperInstance"
CROSS_REF_FILE = "CROSS-REFERENCES.md"

def get_token() -> str:
    """Get GitHub token from env or gh auth"""
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        return token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""

def gh_api(path: str, token: str) -> dict:
    """Call GitHub API"""
    import urllib.request
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  API error: {e}")
        return {}

def gh_api_list(path: str, token: str) -> list:
    """Call GitHub API and return list"""
    import urllib.request
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  API error: {e}")
        return []

def fetch_readme(repo: str, token: str) -> str:
    """Fetch README content from repo"""
    data = gh_api(f"/repos/{ORG}/{repo}/readme", token)
    if not data or "content" not in data:
        return ""
    import base64
    try:
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except Exception:
        return ""

def fetch_meta_headers(repo: str, token: str) -> List[str]:
    """Fetch CROSS-POLLINATE.md and X-Ref meta headers"""
    headers = []
    # Check for cross-references in README
    readme = fetch_readme(repo, token)
    if readme:
        # Find x-ref meta headers
        for line in readme.split("\n"):
            if line.strip().startswith("<!-- x-ref"):
                headers.append(line.strip())
    return headers

def find_cross_refs(text: str, all_repos: Set[str]) -> List[str]:
    """Find references to other SuperInstance repos in text"""
    refs = set()
    for repo in all_repos:
        # Check various reference patterns
        if repo.lower() in text.lower():
            refs.add(repo)
    return sorted(refs)

def fetch_all_repos(token: str) -> list:
    """Fetch ALL repos with pagination"""
    import urllib.request
    all_repos = []
    page = 1
    while True:
        data = gh_api_list(f"/users/{ORG}/repos?per_page=100&sort=pushed&page={page}", token)
        if not data:
            break
        all_repos.extend(data)
        page += 1
        if len(data) < 100:
            break
    return all_repos


def main():
    token = get_token()
    if not token:
        print("❌ No GitHub token found. Set GITHUB_TOKEN or run via gh.")
        sys.exit(1)
    
    print(f"🔍 Scanning {ORG} organization...")
    
    # Fetch all repos
    repos = fetch_all_repos(token)
    
    if not repos:
        print("❌ No repos found — check token and org name.")
        sys.exit(1)
    
    print(f"📚 Found {len(repos)} repos")
    
    all_repo_names = {r["name"] for r in repos if not r.get("fork")}
    repo_topics = {}
    
    for r in repos:
        if not r.get("fork"):
            repo_topics[r["name"]] = r.get("topics", [])
    
    # Scan each repo
    cross_refs: Dict[str, Set[str]] = {}
    meta_headers: Dict[str, List[str]] = {}
    readmes: Dict[str, str] = {}
    
    for i, repo in enumerate(sorted(all_repo_names)):
        if (i + 1) % 25 == 0:
            print(f"  [{i+1}/{len(all_repo_names)}] scanning...")
        
        readme = fetch_readme(repo, token)
        readmes[repo] = readme
        
        if readme:
            refs = find_cross_refs(readme, all_repo_names - {repo})
            if refs:
                cross_refs[repo] = set(refs)
        else:
            print(f"  ⚠️ {repo}: no README")
        
        hdrs = fetch_meta_headers(repo, token)
        if hdrs:
            meta_headers[repo] = hdrs
    
    # Find orphan repos (no refs to or from)
    referenced = set()
    for refs in cross_refs.values():
        referenced.update(refs)
    
    all_referenced = referenced | set(cross_refs.keys())
    orphans = sorted(all_repo_names - all_referenced)
    
    # Generate report
    output = f"""# CROSS-REFERENCES — Auto-generated Index

> **Generated:** {os.popen('date -u').read().strip()}
> **Organization:** {ORG}
> **Repos scanned:** {len(all_repo_names)}
> **Repos with refs:** {len(cross_refs)}
> **Orphan repos (no refs):** {len(orphans)}

---

## Cross-Reference Map

"""
    
    for repo in sorted(cross_refs.keys()):
        refs = cross_refs[repo]
        topics = repo_topics.get(repo, [])
        topic_str = f" [{', '.join(topics[:3])}]" if topics else ""
        
        output += f"### {ORG}/{repo}{topic_str}\n\n"
        output += "**References from this repo:**\n"
        for ref in sorted(refs):
            output += f"- [{ref}](https://github.com/{ORG}/{ref})\n"
        output += "\n"
    
    output += """---

## Missing Meta-Headers

Repos without `<!-- x-ref -->` meta headers in their README:

"""
    
    # Check which repos have meta headers
    for repo in sorted(all_repo_names):
        readme = readmes.get(repo, "")
        has_meta = any("x-ref" in line.lower() for line in readme.split("\n"))
        if not has_meta:
            output += f"- [{repo}](https://github.com/{ORG}/{repo}) — no meta-header\n"
    
    output += """
---

## Orphan Repos (No Cross-References Found)

*These repos don't reference or get referenced by any other {ORG} repo.*

"""
    for repo in orphans:
        topics = repo_topics.get(repo, [])
        topic_str = f" ({', '.join(topics[:3])})" if topics else ""
        output += f"- [{repo}](https://github.com/{ORG}/{repo}){topic_str}\n"
    
    output += """
---

## Stats

| Metric | Count |
|--------|-------|
| Total repos | {len(all_repo_names)} |
| With cross-refs | {len(cross_refs)} |
| Orphan repos | {len(orphans)} |
| With meta-headers | {len(meta_headers)} |
"""
    
    # Write output
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", CROSS_REF_FILE)
    with open(out_path, "w") as f:
        f.write(output)
    
    print(f"\n✅ Generated {CROSS_REF_FILE}")
    print(f"   {len(cross_refs)} repos with cross-refs")
    print(f"   {len(orphans)} orphan repos (no refs)")
    print(f"   {len(meta_headers)} repos with meta-headers")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
