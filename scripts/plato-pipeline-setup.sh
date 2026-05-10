#!/usr/bin/env bash
# PLATO Data Pipeline — Setup Script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PIPELINE_SCRIPT="$SCRIPT_DIR/plato-pipeline.py"

echo "=== PLATO Data Pipeline Setup ==="

# 1. Create data directories
echo "Creating data directories..."
sudo mkdir -p /data/plato-ingest
sudo mkdir -p /data/plato-training
sudo mkdir -p /data/plato-training/manifests
sudo chown -R ubuntu:ubuntu /data/plato-ingest /data/plato-training

# 2. Initialize pipeline state
if [ ! -f /data/plato-ingest/pipeline-state.json ]; then
    echo '{"last_run":null,"tile_ids_seen":[]}' > /data/plato-ingest/pipeline-state.json
    echo "Initialized pipeline state"
fi

# 3. Make pipeline script executable
chmod +x "$PIPELINE_SCRIPT"
echo "Pipeline script: $PIPELINE_SCRIPT"

# 4. Install systemd timer
echo "Installing systemd timer..."

# Write the service file
sudo tee /etc/systemd/system/plato-pipeline.service > /dev/null <<SERVICEEOF
[Unit]
Description=PLATO Data Pipeline Worker
Documentation=https://github.com/superinstance/ai-pages
After=network.target

[Service]
Type=oneshot
User=ubuntu
Group=ubuntu
WorkingDirectory=$WORKSPACE_DIR
ExecStart=$PIPELINE_SCRIPT
StandardOutput=append:/var/log/plato-pipeline.log
StandardError=append:/var/log/plato-pipeline.log

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Write the timer file
sudo tee /etc/systemd/system/plato-pipeline.timer > /dev/null <<TIMEREOF
[Unit]
Description=Run PLATO Data Pipeline hourly
Requires=plato-pipeline.service

[Timer]
OnCalendar=hourly
Persistent=true
OnBootSec=5min

[Install]
WantedBy=timers.target
TIMEREOF

# 5. Reload systemd and enable timer
echo "Enabling and starting timer..."
sudo systemctl daemon-reload
sudo systemctl enable plato-pipeline.timer
sudo systemctl start plato-pipeline.timer

# 6. Verify timer status
echo ""
echo "=== Timer Status ==="
systemctl status plato-pipeline.timer --no-pager 2>&1 || true

echo ""
echo "=== Setup Complete ==="
echo "  Service:  plato-pipeline.service"
echo "  Timer:    plato-pipeline.timer (runs hourly, +5min boot delay)"
echo "  Log:      /var/log/plato-pipeline.log"
echo ""
echo "Running first pipeline pass now..."

# 7. Run first pass
python3 "$PIPELINE_SCRIPT"
rc=$?
echo ""
if [ $rc -eq 0 ]; then
    echo "✓ First pipeline pass completed successfully"
else
    echo "✗ First pipeline pass exited with code $rc"
fi
exit $rc
