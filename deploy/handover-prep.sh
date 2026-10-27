#!/usr/bin/env bash
# BJ runs this BEFORE exporting/sending the LXC. It removes every credential and personal link
# so the new owner starts clean. Safe to run twice. Run as root.
set -uo pipefail
echo "Stopping sync + tunnel..."
systemctl disable --now sme-sync.timer cloudflared 2>/dev/null
cloudflared service uninstall 2>/dev/null
echo "Removing Cloudflare tunnel credentials..."
rm -rf /etc/cloudflared /root/.cloudflared /home/*/.cloudflared
echo "Removing Mnemosyne key and the vault checkout..."
shred -u /var/lib/sme/.ssh/mnemosyne_deploy* 2>/dev/null; rm -rf /var/lib/sme/.ssh /var/lib/sme/mnemosyne
sed -i 's/^MNEMO_ENABLED=.*/MNEMO_ENABLED=0/' /etc/sme/sme.env
echo "Clearing builds, logs, shell history..."
rm -rf /var/lib/sme/releases/* /var/lib/sme/.fingerprint
journalctl --rotate >/dev/null 2>&1; journalctl --vacuum-time=1s >/dev/null 2>&1
rm -f /root/.bash_history /var/lib/sme/.bash_history
echo
echo "REMINDER (cannot be done from inside the LXC):"
echo "  1. GitHub > jerrekt/mnemosyne > Settings > Deploy keys: delete the 'sme-lxc-readonly' key."
echo "  2. Cloudflare Zero Trust > Tunnels: delete (or rotate) the tunnel this LXC used."
echo "  3. Then shut down and export:  vzdump <CTID> --mode stop --compress zstd"
