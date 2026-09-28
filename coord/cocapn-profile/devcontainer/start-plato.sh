#!/bin/bash
# Start PLATO environment in Codespaces
echo "🏛️ Starting PLATO Room Server..."
python3 scripts/plato-room-server.py &
sleep 2

echo "🎮 Starting Holodeck MUD on port 7778..."
cargo run --release &
sleep 3

echo "📊 Starting Fleet Dashboard on port 8848..."
python3 scripts/fleet-dashboard.py &
sleep 1

echo ""
echo "⚓ PLATO Environment Ready!"
echo "   MUD:         telnet localhost 7778"
echo "   PLATO API:   http://localhost:8847"
echo "   Dashboard:   http://localhost:8848"
echo ""
echo "   Other vessels can connect if ports are forwarded."
