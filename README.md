# listky.top

**One word. One PIN. Zero bullshit.**

The dumbest, most private, minimalist list-sharing platform on the internet.

You get one word as your username.  
You get a 6-digit PIN (no recovery, no email, no mercy).  
You make lists. Public or private. That's it.

No profiles, no followers, no likes, no analytics cookies, no ads, no tracking pixels, no bullshit.

https://listky.top

## Why this exists

Modern platforms force you to give email, phone, OAuth, birthday, blood type, mother's maiden name, favorite color, and soul just to make a list of movies.  
listky.top is the opposite: maximum identity with minimum data.  
One word claims your namespace forever (first-come-first-served).  
One PIN is your only key — lose it and the account is gone forever.

It's deliberately stupid and brutally honest about privacy.

## Core principles

- **Zero personal data collected** — no email, no name, no phone, no IP stored in plain text (only salted SHA-256 hashes for abuse detection)
- **No account recovery** — if you forget your PIN, your account is lost. We warned you.
- **No tracking** — no Google Analytics, no Meta pixel, no fingerprinting libraries
- **Minimal surface area** — plain text + links only (no image uploads, no rich embeds at v1)
- **Self-hostable first** — the public instance is just one possible deployment
- **AGPL-3.0 licensed** — if someone hosts a public version with changes, they must share the source

## Features (v1 – MVP)

- One-word alphanumeric username signup (3–20 chars, first-come-first-served)
- 6-digit PIN authentication (bcrypt hashed, escalating lockouts after 4 wrong attempts)
- Create/edit/delete lists (public or private)
- List URLs: `https://listky.top/username/list-slug`
- Basic popularity tracking: unique daily IP views (salted hash) for trending section
- Homepage trending: top public lists by unique views (with creator permission toggle)
- No JavaScript required for core usage (progressive enhancement only)
- Form-based signup & list creation (no fancy SPA at v1)

## Planned v2 / nice-to-have (no timeline)

- Markdown support in list content
- List categories/tags
- Export/import (markdown, JSON, CSV)
- Optional recovery codes export at signup (client-side generated, never sent to server)
- Rate limiting on signups & list creation per IP
- Cloudflare Turnstile CAPTCHA on signup
- Simple moderation queue for public lists (report button)
- RSS feed for public user lists
- ActivityPub / fediverse integration (long shot)

## Privacy & Security Design

- **No PII stored** — only username, hashed PIN, salted/hashed last IP, timestamps
- **IP hashing** — SHA-256 + per-install salt (from .env) — not reversible, but enough for rate limiting & view deduplication
- **Lockouts** — 4 fails → 5 min, then 15 min, then longer (stored in DB)
- **No sessions/JWT** — every action requires PIN (stateless, no cookies at v1)
- **Data stored** — SQLite single file (`/app/data/listky.db`) — easy backups
- **No HTTPS inside Docker** — Cloudflare Tunnel handles TLS termination

**You have been warned:**  
This is not a bank vault. If someone shoulder-surfs your PIN or you type it on a compromised device, your account is compromised. There is no reset button.

## Self-hosting / Running your own instance

### Docker (recommended)

```bash
# 1. Clone
git clone https://github.com/sharmalakshay/listky.git
cd listky

# 2. Copy & edit env
cp .env.example .env
# Edit .env: set PROJECT_LOCATION, PIN_SALT, etc.

# 3. Build & run
docker compose up -d --build