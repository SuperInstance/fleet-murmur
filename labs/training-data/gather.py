#!/usr/bin/env python3
"""Gather new training data from fleet sources and append to JSONL files."""
import os, json, glob, hashlib

BASE = "/home/ubuntu/.openclaw/workspace/training-data"
SEEN = os.path.join(BASE, ".seen_hashes")

def load_seen():
    if not os.path.exists(SEEN): return set()
    with open(SEEN) as f: return set(f.read().splitlines())

def mark_seen(h):
    with open(SEEN, "a") as f: f.write(h + "\n")

def hash_content(content):
    return hashlib.md5(content.encode()).hexdigest()[:12]

def gather():
    seen = load_seen()
    new_count = 0
    
    # 1. New achievement files from dojo agents
    for repo in glob.glob("/tmp/dojo-*/ACHIEVEMENTS/*.md"):
        if "README" in repo: continue
        with open(repo) as f: content = f.read()
        h = hash_content(content)
        if h in seen: continue
        agent = repo.split("/")[2].replace("dojo-","").capitalize()
        entry = {
            "instruction": f"Describe a learning achievement by agent {agent} in the fleet dojo.",
            "input": "", "output": content.strip(),
            "metadata": {"agent": agent, "type": "achievement", "hash": h}
        }
        with open(os.path.join(BASE, "achievements/all-achievements.jsonl"), "a") as f:
            f.write(json.dumps(entry) + "\n")
        mark_seen(h)
        new_count += 1
    
    # 2. New diary entries
    for diary in glob.glob("/tmp/dojo-*/DIARY/*.md"):
        if "README" in diary: continue
        with open(diary) as f: content = f.read()
        h = hash_content(content)
        if h in seen: continue
        agent = diary.split("/")[2].replace("dojo-","").capitalize()
        entry = {
            "instruction": f"Write a diary entry from agent {agent} reflecting on their work.",
            "input": "", "output": content.strip(),
            "metadata": {"agent": agent, "type": "diary", "hash": h}
        }
        with open(os.path.join(BASE, "dojo-transcripts/all-dojo.jsonl"), "a") as f:
            f.write(json.dumps(entry) + "\n")
        mark_seen(h)
        new_count += 1
    
    # 3. New captain's log entries
    for log in glob.glob("/home/ubuntu/.openclaw/workspace/captains-log/entries/*.md"):
        with open(log) as f: content = f.read()
        h = hash_content(content)
        if h in seen: continue
        entry = {
            "instruction": "Write a captain's log entry about fleet operations.",
            "input": "", "output": content.strip(),
            "metadata": {"type": "captains_log", "hash": h}
        }
        with open(os.path.join(BASE, "fleet-operations/all-operations.jsonl"), "a") as f:
            f.write(json.dumps(entry) + "\n")
        mark_seen(h)
        new_count += 1
    
    # 4. New research papers
    for paper in glob.glob("/home/ubuntu/.openclaw/workspace/research/*.md"):
        with open(paper) as f: content = f.read()
        h = hash_content(content)
        if h in seen: continue
        title = os.path.basename(paper).replace(".md","").replace("-"," ").title()
        entry = {
            "instruction": f"Write about {title} for a technical audience.",
            "input": "", "output": content.strip(),
            "metadata": {"type": "research", "source": os.path.basename(paper), "hash": h}
        }
        with open(os.path.join(BASE, "research/all-research.jsonl"), "a") as f:
            f.write(json.dumps(entry) + "\n")
        mark_seen(h)
        new_count += 1
    
    print(f"Gathered {new_count} new training entries")
    return new_count

if __name__ == "__main__":
    gather()
