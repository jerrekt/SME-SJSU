# Creating the LXC on Proxmox (Kratos)

The container goes in the `sjsu/sme` resource pool, shown in the Proxmox tree under the `sjsu` tag next to `senior`. It is **unprivileged**, has no nesting, no Tailscale and no shared folders, and its firewall blocks every LAN address. If someone breaks into it, they reach the internet and nothing else.

## 1. Create it (run on the Proxmox host shell)

Pick a free container ID. The ones used on Kratos so far are 150 and 310. Check the template name with `pveam list local`, and the bridge name under the node's Network tab.

```bash
CTID=320
pct create $CTID local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname sjsu-sme --pool sjsu/sme \
  --unprivileged 1 --features nesting=0 \
  --cores 1 --memory 512 --swap 256 --rootfs local-lvm:4 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp,firewall=1 \
  --onboot 1 --start 1
```

Give it a fixed address in your router or DHCP server afterwards (optional, since nothing connects to it from the LAN).

## 2. Lock it down with the Proxmox firewall

1. Datacenter, Firewall, Options: Firewall = Yes. On the container, Firewall, Options: Firewall = Yes.
2. Copy `deploy/lxc-firewall.fw` to `/etc/pve/firewall/$CTID.fw` on the Proxmox host, and replace `GATEWAY_IP` with your router (it answers DNS).

What the rules do: nothing may connect in. Going out, the container may use DNS to the router, HTTPS and SSH to GitHub, NTP, and the Cloudflare tunnel ports. It may not reach any other address on your network.

## 3. Install the site (inside the container)

```bash
pct enter $CTID
apt-get update && apt-get install -y git
git clone https://github.com/jerrekt/SME-SJSU.git /root/sjsu-sme
CF_TUNNEL_TOKEN=PASTE_TOKEN_HERE bash /root/sjsu-sme/deploy/setup-lxc.sh
```

In Cloudflare Zero Trust, the tunnel's public hostname for `sjsu-sme.adsuaracloud.com` points to **HTTP `127.0.0.1:8080`**.

## 4. Check

Also test IPv6, where firewalls often leak. From inside the container, `ip -6 addr` should show no address you can reach other machines with. Pinging a LAN or link-local IPv6 address must fail.

```bash
curl -s http://127.0.0.1:8080 | head -5
systemctl list-timers sme-sync.timer
journalctl -u sme-sync -n 10 --no-pager
```

## Giving someone access without giving them Kratos

Create a Proxmox user with the `PVEPoolUser` role on `/pool/sjsu/sme` only. They see and manage this container and nothing else. Never grant it on `/pool/sjsu` or higher: permissions pass down and would also expose `sjsu/senior`. Do not share Tailscale access to the node.
