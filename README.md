# Dealio (DealRadar)

Full-stack, real-time deal tracking application that monitors 96 retailers for steep price drops (50%+), pricing errors, coupon stacking, delivery app glitches, and clearance items. Streams deals live to a dark-mode React dashboard via Server-Sent Events (SSE).

## Features

- **Live Deal Feed** — SSE-powered real-time stream showing deals the instant they're discovered
- **96 Seeded Retailer Sources** — Best Buy, Target, Walmart, Amazon, Newegg, DoorDash, and 90 more across 3 scraping tiers
- **Price Error Detection** — Catches $0.09 coffee glitches, 90%+ sudden drops, and pricing mistakes on every price update
- **Amazon Coupon Detection** — Scrapes coupon checkbox elements, combines with promo codes for true final price
- **DoorDash Glitch Monitoring** — Watches delivery apps for items priced at fractions of retail
- **Deal Scoring (0-100)** — Weighted algorithm: discount depth, price history confidence, stock urgency, source reliability, deal type, recency
- **Own Price History** — Builds history from day one for historical low detection after 30 days
- **Coupon Code Database** — Tracks working promo codes per retailer with one-click copy
- **Zero API Keys Required** — Works immediately with free/public sources (Best Buy, Target, Slickdeals RSS, DealNews RSS, Woot)
- **API Key Directory** — 25+ optional integrations with searchable directory, test connection, health indicators
- **Mobile Responsive** — Full functionality on phone, dark mode default
- **Docker Compose** — One command to run everything

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy async, PostgreSQL |
| Task Queue | Celery 5 + Redis broker |
| Scraping | Playwright (browser), aiohttp (API), feedparser (RSS) |
| Real-time | Server-Sent Events (SSE) via Redis pub/sub |
| Frontend | React 18, Vite, TailwindCSS, Recharts, React Query |
| Infrastructure | Docker Compose (6 services) |

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — the defaults work for development

# 2. Start all services
docker compose up --build

# 3. Access the app
# Dashboard: http://localhost:5173
# API: http://localhost:8000/api/health
# API docs: http://localhost:8000/docs
```

The app immediately seeds 96 retailers and starts scanning Tier 1 sources. Deals appear in the live feed within minutes.

## Architecture

```
┌─────────────┐     ┌──────────┐     ┌──────────┐
│   Frontend   │────>│  FastAPI  │────>│ Postgres │
│  React+Vite  │<──SSE│   API    │     │  Schema  │
│  :5173       │     │  :8000   │     │  :5432   │
└─────────────┘     └────┬─────┘     └──────────┘
                         │
                    ┌────┴─────┐
                    │  Redis   │
                    │  :6379   │
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────┴───┐ ┌───┴────┐ ┌──┴───┐
         │ Worker │ │ Worker │ │ Beat │
         │(scrape)│ │(scrape)│ │(cron)│
         └────────┘ └────────┘ └──────┘
```

## Scraper Tiers

| Tier | Method | Interval | Retailers |
|------|--------|----------|-----------|
| 1 | API/RSS | 15 min | Best Buy, Target, Walmart, Amazon, Slickdeals, DealNews, Woot |
| 2 | Playwright | 2 hours | Newegg, B&H Photo, Home Depot, Costco, GameStop, Dell, Lenovo, Staples |
| 3 | Mixed | 4 hours | DoorDash, Apple Refurb, Best Buy Outlet, Dell Outlet, Keepa*, Rainforest*, Microsoft Store |

\* Requires API key

## Deal Scoring Algorithm

Each deal gets a score 0-100 based on:

| Factor | Weight | Details |
|--------|--------|---------|
| Discount Depth | 30 pts | Linear scale: 50% off = 15pts, 90%+ = 30pts |
| Price History | 20 pts | More own data points = higher confidence |
| Stock Urgency | 15 pts | In stock = 10, low stock = 15 |
| Source Reliability | 15 pts | Tier 1 = 15, Tier 2 = 10, Tier 3 = 7 |
| Deal Type | 10 pts | Price error/glitch = 10, clearance = 7 |
| Recency | 10 pts | <1hr = 10, <6hr = 7, <24hr = 5 |
| Historical Low | +5 bonus | Lowest price ever in own database |

## API Keys (Optional)

The app works with zero configuration. Add keys to unlock more sources:

1. Go to **Settings > API Keys**
2. Browse the searchable directory of 25+ data sources
3. Click "Get Key" for signup links, "Add Key" to configure
4. Use "Test Connection" to verify

Priority keys to add:
- **Keepa** ($19/mo) — Full Amazon price history, the crown jewel
- **Discord Webhook** (free) — Get deal alerts in your Discord
- **ScraperAPI** (free tier) — Higher success rates for browser scraping

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers (deals, products, retailers, SSE, etc.)
│   │   ├── core/         # Config, database, security, Redis, deal scoring
│   │   ├── models/       # SQLAlchemy models (8 tables)
│   │   ├── scrapers/     # One file per retailer (21 scrapers)
│   │   └── tasks/        # Celery tasks and beat schedule
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # DealCard, FilterBar, LiveFeed, PriceHistory, etc.
│   │   ├── hooks/        # useDeals, useSSE, useDarkMode, etc.
│   │   └── pages/        # Dashboard, Settings
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## Database Schema

- **retailers** — 96 seeded sources with tier, scrape interval, status
- **products** — Tracked items with prices, coupon codes, true final price
- **price_history** — Every price observation for historical analysis
- **deals** — Active deals with scores, types, coupon codes
- **scrape_jobs** — Audit trail of every scraper run
- **api_keys** — Encrypted storage for configured API keys
- **coupons** — Coupon code database per retailer

## Development

```bash
# Run just the backend (hot reload)
docker compose up api postgres redis

# Run just the frontend
cd frontend && npm run dev

# Trigger a manual scrape
curl -X POST http://localhost:8000/api/retailers/best-buy/scrape

# Watch the SSE stream
curl http://localhost:8000/api/deals/stream
```

## License

MIT
