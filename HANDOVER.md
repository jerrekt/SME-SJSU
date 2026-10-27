# Taking over the SME San Jose State website

For the next officers. No server experience needed to update content. Server steps are copy-paste.

## 1. How it works

```
You edit a file on GitHub
        |
GitHub repo (sjsu-sme)  --->  LXC container (Proxmox)  --->  Cloudflare Tunnel  --->  your domain
                                 every minute it:
                                 1. pulls the repo
                                 2. rebuilds the pages
                                 3. swaps them in (old site stays up if the build fails)
```

- The site is plain HTML. There is no database and nothing to hack into. Caddy serves the files.
- Only `127.0.0.1:8080` inside the container listens. The Cloudflare Tunnel is the only way in, so you open no ports on your router.
- Change a file in the repo, wait about a minute, refresh the site.

## 2. Day-to-day: updating content (no server access needed)

Edit these files in the GitHub web editor (pencil icon), commit to `main`:

| What | File |
|---|---|
| Officers and faculty advisor (do this every year) | `data/officers.json` |
| Events (past ones move to "Past events" by themselves) | `data/events.json` |
| Home text, mission, join steps, contact info, sponsors | `data/site.json` |
| Colors and look | `static/style.css` (the color variables are at the top) |

Fields still set to `null` are hidden on the site until you fill them in. Fill these first:
`contact.email`, `contact.discord_url`, `contact.meetings`, the three links in `join.steps`, `club_presentation_url`, `pitch_video_youtube_id` and `sponsors.partners`.

If you break the JSON, the build fails and the old site stays live. Check the error with step 8.

## 3. Receiving the LXC and connecting your Cloudflare

You need: a Proxmox host, a free Cloudflare account, and a domain on Cloudflare (Cloudflare Registrar sells them, about $10 a year).

1. Restore the container backup you were given:
   ```bash
   pct restore 200 /path/to/vzdump-lxc-XXX.tar.zst --storage local-lvm
   pct start 200 && pct enter 200
   ```
   Use any free container ID instead of 200. The container needs internet access.
   To lock it down so it cannot reach the rest of your network, follow `deploy/proxmox.md` (firewall template included).
2. Check it works locally (inside the container):
   ```bash
   curl -s http://127.0.0.1:8080 | head
   systemctl list-timers sme-sync.timer
   ```
3. Create your tunnel. In Cloudflare: **Zero Trust, Networks, Tunnels, Create a tunnel, Cloudflared**. Name it `sme`. Copy the token it shows.
4. Install it inside the container:
   ```bash
   cloudflared service install PASTE_TOKEN_HERE
   ```
5. In the tunnel's **Public Hostname** tab add your hostname (for example `sme.yourdomain.org`) with service **HTTP**, URL `localhost:8080`.
6. Open the hostname in a browser. Done.

## 4. Changing the domain later

Only Cloudflare knows the domain. Change the Public Hostname in the tunnel (step 3.5). Nothing in the container needs to change.
Optionally update `hostname` in `data/site.json`. It is informational.

## 5. Own the code (do this in your first week)

The code lives at `github.com/jerrekt/SME-SJSU`, BJ's account. Move it to the club:

1. In GitHub, create an organization or use the club's account, then **Settings, Transfer** the repo (or fork it).
2. In the container edit `/etc/sme/sme.env` and set `SITE_REPO` to the new URL. Keep it public so no key is needed.
3. `systemctl start sme-sync`. Check the log (step 8).
4. Make at least two people admins of the repo and of the Cloudflare account. Officers graduate, accounts should not.

## 6. The Spartan Signs section

The Spartan Signs page is the club's project, hosted separately at its own address, and this site only links to it.
It gets live info from two places:

- The public repo `jerrekt/Spartan-signs`: the "Latest updates" list. If the repo moves, set `SIGNS_REPO` in `/etc/sme/sme.env`.
- BJ's private notes (Mnemosyne): status text and the screenshot. **You will not have access to these.** The handover container ships with `MNEMO_ENABLED=0`, so the site uses the fallback text in `data/site.json`. Update that text by hand, or point the build at a new source.

## 7. Yearly handoff checklist

- [ ] Update `data/officers.json`.
- [ ] Add the new officers as admins of the GitHub repo and the Cloudflare account. Remove the old ones.
- [ ] Update `contact`, `join` links and the faculty advisor.
- [ ] Rotate the Cloudflare tunnel token if anyone who had it left (Cloudflare, Tunnels, your tunnel, Refresh token, then re-run `cloudflared service install`).
- [ ] Write down who has the Proxmox login.

## 8. When something looks wrong

Inside the container:

```bash
journalctl -u sme-sync -n 30 --no-pager      # did the last update work? errors show here
systemctl status caddy cloudflared           # are the web server and tunnel up?
sudo -u sme /var/lib/sme/sjsu-sme/deploy/sync.sh   # run an update right now
```

Roll back to the previous build in seconds:

```bash
ls -1t /var/lib/sme/releases                 # newest first; the last 3 are kept
ln -sfn /var/lib/sme/releases/<older-folder> /var/www/sjsu-sme
```

Test a change on your own computer without a server (needs Python 3):

```bash
python3 build/build.py     # writes dist/; open dist/index.html in a browser
```

The footer of every page shows the build time and the commit IDs, so you can tell whether a change went live.

## 9. Rules to keep it safe

- Never put passwords, keys or tokens in the repo. It is public.
- Do not open ports on the router. The tunnel is the only way in.
- Do not publish anyone's phone number or personal email. Officer school emails are fine with their consent.
- Keep dependencies at zero. If you add a tool, someone has to maintain it every year.
- Large changes: use a branch, check it with `python3 build/build.py`, then merge to `main`.

## 10. Building a fresh container from scratch (if the backup is lost)

Debian 12 container, 512 MB RAM, 4 GB disk, then inside it as root:

```bash
apt-get update && apt-get install -y git
git clone https://github.com/jerrekt/SME-SJSU.git /root/sjsu-sme
CF_TUNNEL_TOKEN=PASTE_TOKEN_HERE bash /root/sjsu-sme/deploy/setup-lxc.sh
```

That installs everything (web server, sync timer, tunnel). Leave `CF_TUNNEL_TOKEN` out to skip the tunnel and add it later with step 3.
