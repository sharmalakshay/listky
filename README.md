# listky.top

**One word. One PIN. Zero bullshit.**

The dumbest, most private, minimalist list-sharing platform on the internet.

You get one word as your username.  
You get a 6-digit PIN (no recovery, no email, no mercy).  
You make lists. Public or private. That's it.

No forced profiles, no surveillance tracking, no algorithmic manipulation, no data harvesting, no bullshit.

When you want powerful features (voting, discovery, analytics), they're there. When you want total privacy, that's respected too.

https://listky.top

## Why this exists

Modern platforms force you to give email, phone, OAuth, birthday, blood type, mother's maiden name, favorite color, and soul just to make a list of movies.  
listky.top is the opposite: maximum identity with minimum friction.  
One word claims your namespace forever (first-come-first-served).  
One PIN is your only key - lose it and the account is gone forever.

**Start simple, scale powerful.**  
We begin with radical simplicity to build trust, then add features that make your lists discoverable, credible, and viral - but only if you want them to be.

It's deliberately stupid and brutally honest about privacy.

## Core principles

- **Zero personal data collected** - no email, no name, no phone, no IP stored in plain text (only salted SHA-256 hashes for abuse detection)
- **No account recovery** - if you forget your PIN, your account is lost. We warned you.  
- **No tracking** - no Google Analytics, no Meta pixel, no fingerprinting libraries
- **Dual privacy approach** - Maximum privacy protection for private lists, maximum discoverability for public lists (user's choice)
- **No friction signup** - One word + 6 digits. No email verification, no captcha, no bullshit
- **Self-hostable first** - the public instance is just one possible deployment
- **Hybrid open source** - Core platform AGPL-3.0 licensed, premium features proprietary
- **Self-hostable forever** - The full-featured core will always be free to run yourself

## Features (v1 – MVP)

- One-word alphanumeric username signup (3–20 chars, first-come-first-served)
- 6-digit PIN authentication (bcrypt hashed, escalating lockouts after 4 wrong attempts)
- Create/edit/delete lists (public or private)
- List URLs: `https://listky.top/username/list-slug`
- Basic popularity tracking: unique daily IP views (salted hash) for trending section
- Homepage trending: top public lists by unique views (with creator permission toggle)
- No JavaScript required for core usage (progressive enhancement only)
- Form-based signup & list creation (no fancy SPA at v1)

## Vision & Roadmap

**Short-term goal:** Build trust through radical simplicity and privacy
**Long-term vision:** Become the global platform for lists - every person on the planet using listky.top for both personal and professional/commercial use cases

### Dual Privacy Approach
We serve two types of users equally well:
- **Privacy-focused users:** Maximum privacy protection, private lists, zero tracking
- **Public/viral users:** Maximum SEO optimization, discoverability, social features, trending algorithms

### The Strategy
1. **Start minimal** → Build trust with zero friction signup and bulletproof privacy
2. **Add power features** → Rich functionality behind the simple interface
3. **Scale viral mechanics** → Voting, trending, SEO, social sharing for public lists
4. **Global adoption** → Personal lists (shopping, todos) + Professional lists (rankings, reviews, guides)

## Planned Features Roadmap

### v2 - Enhanced Experience
- **Rich text editing** - Simple formatting (bold, italic, headers) with progressive enhancement
- **List categories/tags** - Organization and discoverability 
- **Export/import** - Markdown, JSON, CSV support
- **Optional recovery codes** - Client-side generated, never sent to server
- **Rate limiting** - Per-IP limits on signups & list creation

### v3 - Social & Credibility 
- **Voting system** - Thumbs up/down on public lists to gauge credibility
- **List validation** - Community-driven accuracy scoring ("Top 10 Hollywood movies" gets voted on for validity)
- **Comments/reactions** - Simple feedback system for public lists
- **User reputation** - Based on list quality and votes received
- **Advanced search** - Filter by tags, votes, credibility scores

### v4 - Viral & Professional
- **SEO optimization** - Rich snippets, social meta tags, structured data for public lists
- **Trending algorithms** - Beyond simple view counts - viral potential scoring
- **Social sharing** - One-click sharing with beautiful link previews
- **Commercial features** - Verified accounts, sponsored list placement, list monetization
- **API access** - For businesses to integrate list data
- **Mobile apps** - iOS/Android for broader reach

### v5 - Platform Domination
- **Collaborative lists** - Multiple editors, suggested changes, version control
- **List templates** - Quick-start templates for common list types
- **Embeddable lists** - Embed public lists on other websites
- **Advanced analytics** - Public list performance metrics (for creators who want them)
- **List marketplace** - Curated, premium list content
- **Enterprise features** - Team accounts, advanced privacy controls

## Key Feature Deep Dive

### Voting & Credibility System
**The Problem:** Anyone can make a list claiming "Top 10 X of all time" but how do you know if it's credible?

**The Solution:** Community validation through voting
- Users can vote 👍/👎 on public lists (opt-in by list creators)
- Credibility score = (upvotes - downvotes) / total_votes
- Lists display credibility indicators: ⭐⭐⭐⭐⭐ (highly validated) vs ⚠️ (community disagrees)
- Search/trending algorithms factor in credibility scores
- List creators can choose to enable/disable voting per list

**Use Cases:**
- "Top 10 Restaurants in NYC" gets voted on by locals who've been there
- "Best Programming Languages to Learn" validated by developers
- "Movies to Watch This Weekend" gets thumbs up from people who watched them
- Personal lists (private or public without voting enabled) remain unaffected

### SEO & Viral Mechanics (Future)
- **Rich snippets** - Lists show up beautifully in Google search results
- **Social meta tags** - Perfect previews when shared on Twitter, LinkedIn, etc.
- **Structured data** - Machine-readable list markup for search engines  
- **Viral scoring** - Algorithm considers votes, views, shares, recency, engagement
- **Cross-platform sharing** - One-click sharing with automatic link previews

## Privacy & Security Design

- **No PII stored** - only username, hashed PIN, salted/hashed last IP, timestamps
- **IP hashing** - SHA-256 + per-install salt (from .env) - not reversible, but enough for rate limiting & view deduplication
- **Lockouts** - 4 fails → 5 min, then 15 min, then longer (stored in DB)
- **No sessions/JWT** - every action requires PIN (stateless, no cookies at v1)
- **Data stored** - SQLite single file (`/app/data/listky.db`) - easy backups
- **No HTTPS inside Docker** - Cloudflare Tunnel handles TLS termination

**You have been warned:**  
This is not a bank vault. If someone shoulder-surfs your PIN or you type it on a compromised device, your account is compromised. There is no reset button.

## Business Model & Licensing

### Hybrid Open Source Approach
**Core Platform (Always Free & Open):**
- User accounts, list creation, basic privacy features
- Voting system, community validation  
- Core API, self-hosting capabilities
- Licensed under AGPL-3.0 - always free to use and modify

**Premium Features (Proprietary SaaS):**
- Advanced analytics dashboard for list creators
- Enhanced SEO optimization and rich snippets
- Enterprise team management and collaboration tools  
- Priority support and managed hosting
- White-label self-hosting options

**Why This Model:**
- ✅ **Trust through transparency** - Core privacy/security code is auditable
- ✅ **Global adoption** - Self-hosting removes single point of failure  
- ✅ **Sustainable revenue** - Premium features fund continued development
- ✅ **Community contributions** - Open source core benefits from contributors
- ✅ **Both worlds** - Users get powerful free tools + optional premium features

### Revenue Streams
1. **Hosted service** - listky.top premium accounts
2. **Enterprise features** - Advanced collaboration, analytics, support
3. **API access** - Commercial usage of the listky platform
4. **Whitelabel hosting** - Managed listky instances for organizations

## Technical Implementation: Hybrid Open/Private Model

### Repository Structure
```
listky/                          (this repo - AGPL-3.0)
├── core/                        # Core platform (always open)
│   ├── database.py             # User accounts, lists, voting
│   ├── auth.py                 # PIN authentication
│   ├── api/                    # Public API endpoints
│   └── privacy.py              # Privacy/security features
├── web/                        # Basic web interface (open)
│   ├── templates/              # HTML templates
│   └── static/                 # CSS, basic JS
└── config/                     # Self-hosting configs (open)

listky-premium/                  (private repo)
├── analytics/                  # Advanced analytics dashboard  
├── seo/                       # Rich snippets, social meta
├── enterprise/                # Team management, collaboration
├── api-gateway/               # Rate limiting, commercial API
└── deployment/                # Managed hosting infrastructure
```

### Integration Pattern
**Plugin Architecture:**
- Core platform exposes hooks/events: `on_list_created`, `on_list_viewed`, etc.
- Premium features register as plugins that listen to these events
- Core platform has simple config: `enable_premium_features: true/false`

**API-First Design:**  
- Core platform exposes REST/GraphQL API
- Premium features are separate microservices that call core API
- Self-hosted instances run core only, hosted service runs core + premium

**Database Separation:**
- Core database: users, lists, votes (always in open source)
- Premium database: analytics, enterprise data (private)
- Clear API boundaries between the two

### Development Workflow
1. **All privacy/security features** → Always in open source core
2. **All basic functionality** → Always in open source core  
3. **Advanced/enterprise features** → Private premium repository
4. **No vendor lock-in** → Self-hosted instances are fully functional
5. **Premium value-add** → Analytics, SEO, collaboration that enhance but don't replace core features

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