#!/usr/bin/env bash
# One-time setup inside a fresh Debian 12 LXC. Run as root:  bash setup-lxc.sh
# It installs everything, creates the 1-minute sync, and (optionally) the Cloudflare tunnel. No keys or private repos are needed.
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "run as root"; exit 1; }
HERE=$(cd "$(dirname "$0")" && pwd)
SITE_REPO=${SITE_REPO:-https://github.com/jerrekt/SME-SJSU.git}
SIGNS_REPO=${SIGNS_REPO:-https://github.com/jerrekt/Spartan-signs.git}

apt-get update -qq
apt-get install -y -qq git python3 caddy curl openssh-client util-linux ca-certificates

id sme >/dev/null 2>&1 || useradd --system --create-home --home-dir /var/lib/sme --shell /usr/sbin/nologin sme
install -d -o sme -g sme /var/lib/sme/releases /var/www
install -d -m 755 /etc/sme

[ -f /etc/sme/sme.env ] || cat > /etc/sme/sme.env <<EOF
SITE_REPO=$SITE_REPO
SITE_BRANCH=main
SIGNS_REPO=$SIGNS_REPO
EOF

as_sme() { runuser -u sme -- "$@"; }
[ -d /var/lib/sme/sjsu-sme/.git ] || as_sme git clone --depth 20 "$SITE_REPO" /var/lib/sme/sjsu-sme
[ -d /var/lib/sme/spartan-signs/.git ] || as_sme git clone --depth 20 "$SIGNS_REPO" /var/lib/sme/spartan-signs

install -m 644 /var/lib/sme/sjsu-sme/deploy/Caddyfile /etc/caddy/Caddyfile
install -m 644 /var/lib/sme/sjsu-sme/deploy/sme-sync.service /etc/systemd/system/
install -m 644 /var/lib/sme/sjsu-sme/deploy/sme-sync.timer /etc/systemd/system/
chmod +x /var/lib/sme/sjsu-sme/deploy/*.sh
systemctl daemon-reload
systemctl enable --now caddy
systemctl restart caddy
systemctl start sme-sync.service || true       # first build now
systemctl enable --now sme-sync.timer

if [ -n "${CF_TUNNEL_TOKEN:-}" ]; then
  curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg -o /usr/share/keyrings/cloudflare-main.gpg
  echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main" > /etc/apt/sources.list.d/cloudflared.list
  apt-get update -qq && apt-get install -y -qq cloudflared
  cloudflared service uninstall >/dev/null 2>&1 || true
  cloudflared service install "$CF_TUNNEL_TOKEN"
  echo "Tunnel installed. In Cloudflare Zero Trust, set the tunnel's public hostname to HTTP  127.0.0.1:8080"
else
  echo "No CF_TUNNEL_TOKEN given: site is only on 127.0.0.1:8080. See HANDOVER.md step 3 to connect Cloudflare."
fi
echo; echo "Done. Check:  curl -s http://127.0.0.1:8080 | head   and   systemctl list-timers sme-sync.timer"
