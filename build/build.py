#!/usr/bin/env python3
"""Build the SME San Jose State static site.

Inputs
  data/*.json                 club-owned content (officers, events, site text)
  $MNEMO_DIR                  sparse checkout of the Mnemosyne vault. ONLY the notes in
                              MNEMO_ALLOW are read, and only if their front matter says
                              `public: true`. Anything else in the vault is never touched.
  $SIGNS_DIR                  clone of jerrekt/Spartan-signs (public repo)
Output
  $OUT_DIR                    plain HTML/CSS, served by Caddy
"""
import datetime
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
MNEMO = Path(os.environ.get("MNEMO_DIR", "/var/lib/sme/mnemosyne"))
SIGNS = Path(os.environ.get("SIGNS_DIR", "/var/lib/sme/spartan-signs"))
OUT = Path(os.environ.get("OUT_DIR", ROOT / "dist"))
TZ = ZoneInfo("America/Los_Angeles")

# The only vault files this site may read (user rule: Spartan Signs + SJSU only).
MNEMO_ALLOW = ["projects/sjsu.md", "projects/sme.md", "projects/spartan-sign.md"]
MNEMO_ASSETS = ["images/spartan-sign-control.webp"]

NAV = [
    ("Home", "/"),
    ("Spartan Signs", "/spartan-signs/"),
    ("Events", "/events/"),
    ("Officers", "/officers/"),
    ("Join", "/join/"),
    ("Sponsors", "/sponsors/"),
    ("Contact", "/contact/"),
]

e = html.escape


def load_json(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


# ---------- vault notes (public only) ----------
def parse_front_matter(text):
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        try:
            if v.startswith(("[", '"')):
                v = json.loads(v)
            elif v in ("true", "false"):
                v = v == "true"
        except ValueError:
            v = v.strip('"')
        fm[k.strip()] = v
    return fm, m.group(2)


def load_note(rel):
    if rel not in MNEMO_ALLOW:
        raise SystemExit(f"refusing to read {rel}: not on the allowlist")
    p = MNEMO / rel
    if not p.is_file():
        print(f"warn: {rel} missing, section will be skipped", file=sys.stderr)
        return None
    fm, body = parse_front_matter(p.read_text(encoding="utf-8"))
    if fm.get("public") is not True:
        print(f"warn: {rel} is not public: true, skipping", file=sys.stderr)
        return None
    return {"fm": fm, "body": body}


def section(body, heading):
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    return m.group(1).strip() if m else ""


def inline(s):
    s = e(s)
    s = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", s)
    s = re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', s)
    return s


def md_basic(md):
    out, items = [], []

    def flush():
        if items:
            out.append("<ul class=\"plain\">" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for line in md.splitlines():
        if line.startswith("- "):
            items.append(line[2:])
        elif line.strip():
            flush()
            out.append(f"<p>{inline(line)}</p>")
        else:
            flush()
    flush()
    return "\n".join(out)


# ---------- Spartan-signs repo ----------
def signs_commits(n=8):
    try:
        r = subprocess.run(
            ["git", "-C", str(SIGNS), "log", f"-{n}", "--format=%h\x1f%cI\x1f%s"],
            capture_output=True, text=True, check=True,
        )
    except Exception as ex:  # repo missing or git failure: skip the section
        print(f"warn: spartan-signs log failed: {ex}", file=sys.stderr)
        return []
    rows = []
    for line in r.stdout.splitlines():
        h, when, subj = line.split("\x1f", 2)
        rows.append((h, datetime.datetime.fromisoformat(when).astimezone(TZ), subj))
    return rows


def git_head(path):
    try:
        return subprocess.run(["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "n/a"


# ---------- page shell ----------
def shell(site, slug, title, hero_title, hero_sub, body, built):
    path = "/" if slug == "" else f"/{slug}/"
    nav = "".join(
        f'<li><a href="{p}"{" aria-current=\"page\"" if p == path else ""}>{e(t)}</a></li>' for t, p in NAV
    )
    sub = f"<p>{e(hero_sub)}</p>" if hero_sub else ""
    small = "" if slug == "" else " small"
    heads = f"{git_head(ROOT)}/{git_head(SIGNS)}/{git_head(MNEMO)}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · {e(site['name'])}</title>
<meta name="description" content="{e(site['tagline'][:155])}">
<meta name="theme-color" content="#0B2A5B">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="bar">
<a class="brand" href="/"><span class="mark" aria-hidden="true">sme</span><span>{e(site['name'])}</span></a>
<nav aria-label="Main"><ul>{nav}</ul></nav>
</div></header>
<section class="hero{small}"><div class="in"><h1>{e(hero_title)}</h1>{sub}</div></section>
<main id="main">
{body}
</main>
<footer><div class="in">
<span>{e(site['name'])} · {e(site['chapter'])}</span>
<span>Updated {built:%b %-d, %Y %-I:%M %p} PT · <code>{e(heads)}</code></span>
</div></footer>
</body>
</html>
"""


# ---------- events ----------
def split_events(now):
    evs = load_json("events.json")["events"]
    for ev in evs:
        ev["_dt"] = datetime.datetime.fromisoformat(ev["start"]).replace(tzinfo=TZ)
    up = sorted([x for x in evs if x["_dt"] >= now], key=lambda x: x["_dt"])
    past = sorted([x for x in evs if x["_dt"] < now], key=lambda x: x["_dt"], reverse=True)
    return up, past


def event_html(ev, past):
    when = f"{ev['_dt']:%A, %B %-d, %Y} · {ev['_dt']:%-I:%M %p}"
    if past:
        signup = "This event has passed."
    elif ev.get("signup_url"):
        signup = f'<a href="{e(ev["signup_url"])}">RSVP here</a>'
    else:
        signup = "RSVP link coming soon. Watch Discord."
    return (
        f'<article class="event{" past" if past else ""}"><h3>{e(ev["title"])}</h3><dl>'
        f"<dt>When</dt><dd>{e(when)}</dd><dt>Where</dt><dd>{e(ev.get('where') or 'TBD')}</dd>"
        f"<dt>Sign up</dt><dd>{signup}</dd></dl></article>"
    )


# ---------- pages ----------
def build():
    now = datetime.datetime.now(TZ)
    site = load_json("site.json")
    officers = load_json("officers.json")
    up, past = split_events(now)

    sme = load_note("projects/sme.md")
    sjsu = load_note("projects/sjsu.md")
    sign = load_note("projects/spartan-sign.md")
    sign_fm = sign["fm"] if sign else {}
    live = sign_fm.get("link") or "https://spartan-signs.adsuaracloud.com"
    live = live.rstrip("/")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copy(ROOT / "static" / "style.css", OUT / "style.css")
    for rel in MNEMO_ASSETS:
        src = MNEMO / rel
        if src.is_file():
            shutil.copy(src, OUT / Path(rel).name)

    pages = {}

    # Home
    sme_intro = ""
    if sme:
        first = next((p for p in sme["body"].split("\n\n") if p.strip()), "")
        sme_intro = f"<p>{inline(first.strip())}</p>"
    do = "".join(f"<li><strong>{e(a)}</strong>: {e(b)}</li>" for a, b in site["what_we_do"])
    mis = "".join(f"<li>{e(m)}</li>" for m in site["mission"])
    up_html = "".join(event_html(x, False) for x in up) or (
        '<p class="muted">No events on the calendar right now. Join our Discord to hear about the next one.</p>'
    )
    stage = sign_fm.get("state") or "Prototyping"
    home = f"""
<h2>Building the next generation of manufacturing engineers</h2>
<p class="lead">{e(site['tagline'])}</p>
<h3>What we do</h3><ul class="plain">{do}</ul>
<h3>Our mission</h3><ul class="plain">{mis}</ul>
<h3>About SME</h3>
<p>{e(site['about_sme'])}</p>
{sme_intro}
<h3>Upcoming events</h3>
{up_html}
<p><a class="btn ghost" href="/events/">All events</a></p>
<h3>Our project</h3>
<div class="card gold"><span class="tag gold">{e(stage)}</span><h3>Spartan Signs</h3>
<p>{e(site['spartan_signs']['summary'])}</p>
<a class="btn" href="/spartan-signs/">See the project</a></div>
<h3>Follow us</h3>
<p>Instagram <a href="https://www.instagram.com/{e(site['contact']['instagram'])}/">@{e(site['contact']['instagram'])}</a></p>
"""
    pages[""] = ("Home", "SME San Jose State", site["chapter"], home)

    # Spartan Signs
    ss = site["spartan_signs"]
    how = "".join(f'<div class="card"><h3>{e(a)}</h3><p>{e(b)}</p></div>' for a, b in ss["how_it_works"])
    teams = "".join(
        f'<div class="card"><h3>{e(a)}</h3><p class="muted">{e(b) if b else "Details coming soon."}</p></div>'
        for a, b in ss["teams"]
    )
    fig = ""
    if sign_fm.get("image") and (OUT / Path(sign_fm["image"]).name).is_file():
        fig = (
            f'<figure><img src="/{e(Path(sign_fm["image"]).name)}" alt="{e(sign_fm.get("image_alt", ""))}" loading="lazy">'
            f'<figcaption>{e(sign_fm.get("image_caption", ""))}</figcaption></figure>'
        )
    lists = ""
    if sign_fm.get("done"):
        lists += "<div class=\"card\"><h3>Done</h3><ul class=\"plain\">" + "".join(f"<li>{e(x)}</li>" for x in sign_fm["done"]) + "</ul></div>"
    if sign_fm.get("next"):
        lists += "<div class=\"card\"><h3>Next</h3><ul class=\"plain\">" + "".join(f"<li>{e(x)}</li>" for x in sign_fm["next"]) + "</ul></div>"
    state_txt = sign_fm.get("state", "In progress")
    status_txt = re.sub(rf"^{re.escape(state_txt)}[.:]\s*", "", sign_fm.get("status", ""))
    status = f'<p><span class="tag gold">{e(state_txt)}</span> {e(status_txt)}</p>' if sign_fm else ""
    details = section(sign["body"], "Details") if sign else ""
    details_html = f"<h3>Details</h3>{md_basic(details)}" if details else ""
    log = ""
    commits = signs_commits()
    if commits:
        log = '<h3>Latest updates</h3><ul class="log">' + "".join(
            f'<li><time datetime="{w.isoformat()}">{w:%b %-d, %-I:%M %p}</time><span>{e(s)} <code>{e(h)}</code></span></li>'
            for h, w, s in commits
        ) + "</ul><p class=\"muted\">Pulled live from the Spartan Signs code repository.</p>"
    sp = f"""
<h2>Spartan Signs</h2>
<p class="lead">{e(ss['summary'])}</p>
{status}
<p><a class="btn" href="{e(live)}/">Open the control demo</a><a class="btn ghost" href="{e(live)}/lab/">Build options lab</a><a class="btn ghost" href="{e(live)}/about/">Project page</a><a class="btn ghost" href="{e(ss['repo'])}">Code on GitHub</a></p>
{fig}
<h3>How it works</h3><div class="grid">{how}</div>
<div class="grid">{lists}</div>
{details_html}
<h3>Teams</h3><div class="grid">{teams}</div>
<p class="muted">{e(ss['licensing'])}</p>
{log}
"""
    pages["spartan-signs"] = ("Spartan Signs", "Spartan Signs", "An SME project at San José State", sp)

    # Events
    past_html = "".join(event_html(x, True) for x in past)
    ev = f"""
<h2>Upcoming events</h2>
{up_html}
{"<h3>Past events</h3>" + past_html if past_html else ""}
"""
    pages["events"] = ("Events", "Events", None, ev)

    # Officers
    ppl = "".join(
        f'<div class="card person"><span class="role">{e(o["role"])}</span><b>{e(o["name"])}</b>'
        f'<a href="mailto:{e(o["email"])}">{e(o["email"])}</a></div>'
        for o in officers["officers"]
    )
    adv = officers["advisor"]
    of = f"""
<h2>{e(officers['season'])} officers</h2>
<div class="people">{ppl}</div>
<h3>Faculty advisor</h3>
<div class="card person"><b>{e(adv['name'])}</b><span class="muted">{e(adv['dept'])}</span><a href="mailto:{e(adv['email'])}">{e(adv['email'])}</a></div>
"""
    pages["officers"] = ("Officers", "Officers", None, of)

    # Join
    j = site["join"]
    steps = "".join(
        f"<li>{e(t)}{f' <a href=\"{e(u)}\">Link</a>' if u else ''}</li>" for t, u in j["steps"]
    )
    jb = f"""
<h2>Join SME San Jose State</h2>
<p class="lead">{e(j['intro'])}</p>
<h3>How to join</h3>
<ol class="steps">{steps}</ol>
"""
    pages["join"] = ("Join", "Join", None, jb)

    # Sponsors
    sp_ = site["sponsors"]
    plist = "".join(f"<li>{e(p)}</li>" for p in sp_["partners"])
    contact = site["contact"]
    mail = f'<a href="mailto:{e(contact["email"])}">{e(contact["email"])}</a>' if contact["email"] else \
        f'<a href="mailto:{e(contact["advisor_email"])}">{e(contact["advisor_email"])}</a> (faculty advisor)'
    spb = f"""
<h2>Sponsors and industry partners</h2>
<p class="lead">{e(sp_['intro'])}</p>
{"<ul class=\"plain\">" + plist + "</ul>" if plist else ""}
<h3>Become a sponsor</h3>
<p>{e(sp_['ask'])}</p>
<p>Contact: {mail}</p>
"""
    pages["sponsors"] = ("Sponsors", "Sponsors", None, spb)

    # Contact
    rows = []
    if contact["email"]:
        rows.append(f'<li><strong>Email:</strong> <a href="mailto:{e(contact["email"])}">{e(contact["email"])}</a></li>')
    rows.append(f'<li><strong>Instagram:</strong> <a href="https://www.instagram.com/{e(contact["instagram"])}/">@{e(contact["instagram"])}</a></li>')
    if contact["discord_url"]:
        rows.append(f'<li><strong>Discord:</strong> <a href="{e(contact["discord_url"])}">Join here</a></li>')
    if contact["meetings"]:
        rows.append(f'<li><strong>Meetings:</strong> {e(contact["meetings"])}</li>')
    rows.append(f'<li><strong>Faculty advisor:</strong> {e(contact["advisor"])} (<a href="mailto:{e(contact["advisor_email"])}">{e(contact["advisor_email"])}</a>)</li>')
    ct = f"""
<h2>Get in touch</h2>
<ul class="plain">{"".join(rows)}</ul>
"""
    pages["contact"] = ("Contact", "Contact", None, ct)

    for slug, (title, h1, sub, body) in pages.items():
        doc = shell(site, slug, title, h1, sub, body, now)
        d = OUT / slug if slug else OUT
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(doc, encoding="utf-8")

    nf = shell(site, "404", "Page not found", "Page not found", None,
               '<p class="lead">That page does not exist. <a href="/">Go home</a>.</p>', now)
    (OUT / "404.html").write_text(nf, encoding="utf-8")
    print(f"built {len(pages) + 1} pages into {OUT} (events: {len(up)} upcoming, {len(past)} past; sjsu note: {'yes' if sjsu else 'no'})")


if __name__ == "__main__":
    build()
