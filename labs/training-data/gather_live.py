#!/usr/bin/env python3
"""Capture MUD conversations as training data. Run every 10 minutes."""
import os, json, glob, hashlib
from datetime import datetime

BASE = "/home/ubuntu/.openclaw/workspace/training-data"
LOG_DIR = "/tmp/cocapn-mud/logs"
MUD_DATA = os.path.join(BASE, "fleet-operations/mud-conversations.jsonl")
SEEN = os.path.join(BASE, ".seen_mud_hashes")

def load_seen():
    if not os.path.exists(SEEN): return set()
    with open(SEEN) as f: return set(f.read().splitlines())

def mark_seen(h):
    with open(SEEN, "a") as f: f.write(h + "\n")

def capture_mud_logs():
    """Capture any MUD server logs or conversation transcripts."""
    seen = load_seen()
    new = 0
    
    # Check MUD server log if it exists
    for logfile in glob.glob("/tmp/cocapn-mud/*.log") + glob.glob("/tmp/cocapn-mud/logs/*"):
        if not os.path.exists(logfile): continue
        with open(logfile) as f: content = f.read()
        if len(content) < 50: continue
        
        h = hashlib.md5(content.encode()).hexdigest()[:12]
        if h in seen: continue
        
        # Split into conversation chunks
        lines = content.strip().split("\n")
        chunk = []
        for line in lines:
            chunk.append(line)
            if len(chunk) >= 20:
                text = "\n".join(chunk)
                entry = {
                    "instruction": "This is a MUD conversation between fleet agents. Describe what happened and what was learned.",
                    "input": "",
                    "output": text,
                    "metadata": {"type": "mud_conversation", "source": os.path.basename(logfile), "hash": h, "captured": datetime.utcnow().isoformat()}
                }
                with open(MUD_DATA, "a") as f:
                    f.write(json.dumps(entry) + "\n")
                chunk = []
                new += 1
        
        if chunk:
            text = "\n".join(chunk)
            entry = {
                "instruction": "This is a MUD conversation between fleet agents. Describe what happened and what was learned.",
                "input": "",
                "output": text,
                "metadata": {"type": "mud_conversation", "source": os.path.basename(logfile), "hash": h, "captured": datetime.utcnow().isoformat()}
            }
            with open(MUD_DATA, "a") as f:
                f.write(json.dumps(entry) + "\n")
            new += 1
        
        mark_seen(h)
    
    return new

def capture_git_commits():
    """Capture recent commit messages as training data (agent thought traces)."""
    seen = load_seen()
    new = 0
    
    for repo in ["/tmp/oracle1-vessel", "/tmp/cocapn-mud"]:
        if not os.path.exists(os.path.join(repo, ".git")): continue
        import subprocess
        result = subprocess.run(
            ["git", "log", "--since=1 hour ago", "--pretty=format:%H|%s|%b"],
            capture_output=True, text=True, cwd=repo
        )
        for line in result.stdout.strip().split("\n"):
            if not line or "|" not in line: continue
            parts = line.split("|", 2)
            if len(parts) < 2: continue
            sha, subject = parts[0], parts[1]
            body = parts[2] if len(parts) > 2 else ""
            h = hashlib.md5(sha.encode()).hexdigest()[:12]
            if h in seen: continue
            
            entry = {
                "instruction": "Write a git commit message that describes a meaningful change to an agent fleet system.",
                "input": f"Repo: {os.path.basename(repo)}",
                "output": f"{subject}\n\n{body}" if body else subject,
                "metadata": {"type": "commit_message", "repo": os.path.basename(repo), "sha": sha[:8], "hash": h}
            }
            with open(os.path.join(BASE, "fleet-operations/commit-messages.jsonl"), "a") as f:
                f.write(json.dumps(entry) + "\n")
            mark_seen(h)
            new += 1
    
    return new

if __name__ == "__main__":
    n1 = capture_mud_logs()
    n2 = capture_git_commits()
    if n1 + n2 > 0:
        print(f"{datetime.utcnow().isoformat()}: Captured {n1} MUD entries, {n2} commit entries")
    else:
        print(f"{datetime.utcnow().isoformat()}: No new data")
