#!/usr/bin/env python3
"""acp-bridge.py — Creates a TCP socket bridge to kimi-cli ACP protocol

Listens on port 8881, spawns kimi-cli acp with proper pipes,
and bridges the TCP connection to kimi-cli's stdin/stdout.
"""
import asyncio, subprocess, os, sys

LOG = "/tmp/acp-bridge.log"
log = open(LOG, "a")

async def handle_client(reader, writer):
    """Bridge TCP client to kimi-cli ACP stdin/stdout"""
    log.write(f"Client connected\n")
    log.flush()

    proc = await asyncio.create_subprocess_exec(
        "kimi-cli", "acp",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    log.write(f"Kimi PID: {proc.pid}\n")
    log.flush()

    async def forward_stdin():
        while True:
            data = await reader.read(65536)
            if not data:
                break
            if proc.stdin:
                proc.stdin.write(data)
                await proc.stdin.drain()
        if proc.stdin:
            proc.stdin.close()

    async def forward_stdout():
        while True:
            data = await proc.stdout.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
        writer.close()

    await asyncio.gather(forward_stdin(), forward_stdout())
    await proc.wait()
    log.write(f"Kimi exited: {proc.returncode}\n")
    log.flush()

async def main():
    server = await asyncio.start_server(handle_client, "127.0.0.1", 8881)
    log.write(f"ACP Bridge listening on 8881, PID {os.getpid()}\n")
    log.flush()
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())