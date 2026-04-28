#!/bin/bash
set -e

# Usage: ./deploy.sh <user> <host>
# Example: ./deploy.sh homeassistant homeassistant.local
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <user> <host>"
  exit 1
fi

USER="$1"
HOST_ARG="$2"
HOST="$USER@$HOST_ARG"
REMOTE_DIR="/config/custom_components/sram_axs"

echo "==> Creating remote directories..."
ssh "$HOST" "sudo mkdir -p $REMOTE_DIR/translations && sudo chmod 777 $REMOTE_DIR $REMOTE_DIR/translations"

echo "==> Syncing files..."
rsync -avO --exclude='__pycache__' --exclude='.DS_Store' \
  custom_components/sram_axs/ \
  "$HOST:$REMOTE_DIR/"

echo "==> Done! Reload the integration in HA: Settings → Devices & Services → SRAM AXS → (3 dots) → Reload."
echo "    Or restart HA if this is a first install."
