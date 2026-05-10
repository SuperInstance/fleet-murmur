#!/usr/bin/env python3
"""ccc-launcher2.py — Launches kimi-cli ACP with proper pipes, captures output"""
import subprocess, sys, os, time, signal

log = open("/tmp/ccc-launcher2.log", "w")
log.write(f"Starting CCC at {time.ctime()}\n")
log.flush()

proc = subprocess.Popen(
    ["kimi-cli", "acp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=0
)
log.write(f"CCC PID: {proc.pid}\n")
log.flush()

# Wait 3 seconds, then capture whatever was output
time.sleep(3)
try:
    out, _ = proc.communicate(timeout=1)
    log.write(f"Output: {out}\n")
except subprocess.TimeoutExpired:
    # Still running, capture partial output
    try:
        proc.stdin.close()
        out = proc.stdout.read(4096)
        log.write(f"Partial output: {out}\n")
    except:
        pass
    proc.kill()
    log.write("Killed after 3s\n")

ret = proc.wait()
log.write(f"Exit code: {ret}\n")
log.flush()

# Print the log
with open("/tmp/ccc-launcher2.log") as f:
    print(f.read())