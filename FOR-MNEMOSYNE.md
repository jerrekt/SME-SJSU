# Note for an AI assistant (Claude): what you can take from this repo into Mnemosyne

You are reading this because someone asked you to bring the SME site's facts into the Mnemosyne vault. Read this file first, then read the files listed below. Everything in this repo is public.

## Direction: one way only

- Mnemosyne reads this repo. This repo never reads Mnemosyne.
- Do not add keys, tokens, private notes, IPs or hostnames of the host machine to this repo. It is public and gets handed to the next officers.
- Do not copy anything private from the vault into this repo.
- If a fact on the site is wrong, tell the user and let them change the files here. Do not edit the vault to "fix" the site.

## What this repo is

The website for SME San Jose State University, the SJSU student chapter (S192) of the Society of Manufacturing Engineers. It is plain static HTML built by `build/build.py` and served by Caddy in a Proxmox container behind a Cloudflare Tunnel. A 1-minute timer pulls this repo and `jerrekt/Spartan-signs` and rebuilds only when something changed. The live address is `https://sjsu-sme.adsuaracloud.com`.

Colorway: Spartan classic (navy `#0B2A5B`, gold `#E5A823`, paper `#F7F5EF`).
Tabs: Home, Spartan Signs, Events, Officers, Join, Sponsors, Contact.

## Where the facts live (read these)

| Fact | File |
|---|---|
| Club description, mission, join steps, sponsors text, contact info, Spartan Signs status, Done/Next lists, teams | `data/site.json` |
| Officers and faculty advisor for the current year | `data/officers.json` |
| Events (past ones move to "Past events" on the site by date) | `data/events.json` |
| Colors and layout | `static/style.css` |
| How the build and sync work | `README.md`, `deploy/sync.sh`, `build/build.py` |
| How the next officers take it over | `HANDOVER.md` |

Raw files: `https://raw.githubusercontent.com/jerrekt/SME-SJSU/main/<path>`

The Spartan Signs project code is in the separate public repo `jerrekt/Spartan-signs`. This repo only links to it and shows its recent commits.

## Safe to send into Mnemosyne

All of the facts in the files above are public. In the vault, follow the vault's own conventions (`CONVENTIONS.md` there) and its rule that new notes start as `public: false` unless the user says otherwise.

Suggested shape, one note for the club site and optional updates to the existing SME and Spartan Sign notes:

- A project note, for example `projects/sme-website.md`, with: what it is, the live address, the tabs, the data sources, and who maintains it. Link it to the existing SME and Spartan Sign notes.
- Spartan Sign status: copy `spartan_signs.stage`, `status`, `done` and `next` from `data/site.json` into the vault's Spartan Sign note, so both places say the same thing. Keep the vault's own wording rules.
- Officers: only if the user asks. Names and school emails are public on the site, but keep them out of the vault's public cards unless the user says so.
- Events: summarize upcoming ones only. Past events do not need to live in the vault.

## Keep out of the vault note and out of this repo

- Where the container runs on the home network (host names, addresses, container IDs).
- Cloudflare tunnel names or tokens, deploy keys, any credentials.
- Personal contact details beyond what the site already shows.

## Keeping it current

When `data/*.json` changes in this repo, re-read it before writing to the vault. Do not trust a copy you made earlier. The footer of every page shows the build time and the commit IDs, so you can tell which version is live.
