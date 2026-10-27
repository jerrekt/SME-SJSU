#!/usr/bin/env bash
# BJ runs this BEFORE exporting/sending the LXC. It removes every credential and personal link
# so the new owner starts clean. Safe to run twice. Run as root.
set -uo pipefail
echo "Stopping sync + tunnel..."
systemctl disable --now sme-sync.timer cloudflared 2>/dev/null
cloudflared service uninstall 2>/dev/null
echo "Removing Cloudflare tunnel credentials..."
rm -rf /etc/cloudflared /root/.cloudflared /home/*/.cloudflared
echo "Clearing builds, logs, shell history..."
rm -rf /var/lib/sme/releases/* /var/lib/sme/.fingerprint
journalctl --rotate >/dev/null 2>&1; journalctl --vacuum-time=1s >/dev/null 2>&1
rm -f /root/.bash_history /var/lib/sme/.bash_history
echo
echo "REMINDER (cannot be done from inside the LXC):"
echo "  1. Cloudflare Zero Trust > Tunnels: delete (or rotate) the tunnel this LXC used."
echo "  2. Remove your SSH keys from /root/.ssh/authorized_keys if you added any."
echo "  3. Then shut down and export:  vzdump <CTID> --mode stop --compress zstd"
