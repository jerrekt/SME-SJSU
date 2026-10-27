# SME San Jose State website

Public site for the SJSU student chapter (S192) of the Society of Manufacturing Engineers.
Plain static HTML built by `build/build.py` (Python 3 standard library only), served by Caddy in a Proxmox LXC, published through a Cloudflare Tunnel.

- **Taking it over:** read [HANDOVER.md](HANDOVER.md).
- **AI assistants (Claude):** read [FOR-MNEMOSYNE.md](FOR-MNEMOSYNE.md) before copying anything into BJ's vault.
- **Update content:** edit `data/*.json`, commit to `main`, live in about a minute.
- **Look and feel:** `static/style.css` (Spartan classic: navy, gold, paper).

## Layout

| Path | Purpose |
|---|---|
| `data/` | Officers, events, site text and contact info |
| `static/style.css` | All styling |
| `build/build.py` | Builds the pages into `dist/` |
| `deploy/sync.sh` | Runs every minute: pull, rebuild if changed, atomic swap |
| `deploy/setup-lxc.sh` | One-time setup inside a fresh Debian 12 LXC |
| `deploy/handover-prep.sh` | Strips keys and tokens before the container is passed on |
| `deploy/sme.env.example` | Settings (repo URLs) |

## Data sources

1. This repo (`data/`, `static/`, `build/`): everything the club edits.
2. `jerrekt/Spartan-signs` (public): the "Latest updates" list on the Spartan Signs page.

No keys, tokens or private repos are involved, so the container is safe to pass on.

## Local preview

```bash
SIGNS_DIR=/nonexistent python3 build/build.py && python3 -m http.server -d dist 8000
```
