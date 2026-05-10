#!/usr/bin/env python3
"""ccc-launcher.py — Launches kimi-cli ACP with proper pipe transport"""
import subprocess, sys, os, time

logfile = open("/tmp/ccc-launcher.log", "w")
logfile.write(f"Starting CCC at {time.ctime()}\n")
logfile.flush()

proc = subprocess.Popen(
    ["kimi-cli", "acp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

logfile.write(f"CCC PID: {proc.pid}\n")
logfile.flush()

# Keep the process alive and log output
while True:
    try:
        out = proc.stdout.readline()
        if out:
            logfile.write(f"[STDOUT] {out.strip()}\n")
            logfile.flush()
        err = proc.stderr.readline()
        if err:
            logfile.write(f"[STDERR] {err.strip()}\n")
            logfile.flush()
        ret = proc.poll()
        if ret is not None:
            logfile.write(f"CCC exited with code {ret}\n")
            logfile.flush()
            break
    except Exception as e:
        logfile.write(f"Error: {e}\n")
        logfile.flush()
        break