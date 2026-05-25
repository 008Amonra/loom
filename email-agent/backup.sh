#!/bin/bash
set -e
DEST="/media/jace/tb1/45dgof8-backup/$(date +%Y-%m-%d)"
mkdir -p "$DEST"
tar czf "$DEST/45dgof8-site.tar.gz" -C /home/jace/45dgof8 \
  --exclude=node_modules --exclude='*.mp4' --exclude=telegram-inbox.json .
cp ~/.opencode/secrets.env "$DEST/"
chmod 600 "$DEST/secrets.env"
cp ~/.opencode/opencode.json "$DEST/"
ln -sfn "$DEST" "/media/jace/tb1/45dgof8-backup/latest"
echo "Backup: $DEST"
