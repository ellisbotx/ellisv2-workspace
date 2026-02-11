# Competitor Intelligence — Weekly Tracker

## Overview
Weekly competitive monitoring for Marco's three card game brands on Amazon FBA:
- **Black Owned** — Black culture party/trivia card games
- **Card Plug** — Adult party card games (mainstream)
- **Kinfolk** — Conversation/connection card games

## Schedule
- **Frequency:** Every Monday morning
- **File format:** `YYYY-MM-DD.md` (date of report)
- **Triggered by:** Cron job or manual request

## What We Track

### Per Competitor
- Product name & ASIN
- Current price (and any active deals/coupons)
- Monthly sales signal ("X bought in past month")
- Star rating & review count
- BSR (Best Sellers Rank) when available
- Small Business badge status
- New launches or edition releases

### Category-Level
- Price range trends
- Seasonal promotions (Valentine's, BHM, holidays)
- New entrant alerts
- Review velocity patterns

## Search Queries Used
1. `party card games for adults` (sorted by popularity)
2. `conversation card games for adults`
3. `black culture card games party`
4. `black owned card games party conversation`

## Key Competitors to Always Track

### Black Owned Competitors
| Competitor | ASIN |
|-----------|------|
| Black Card Revoked (Original) | B014YZHW4S |
| Black Card Revoked (5th Ed) | B07ZXR31DL |
| Urban Trivia | B0966DVM2T |
| Black Heritage Trivia | B0DJ4GN9C3 |

### Card Plug Competitors
| Competitor | ASIN |
|-----------|------|
| Cards Against Humanity | B004S8F7QM |
| Ransom Notes | B09F9XMRG5 |
| Secret Hitler | B01JKD4HYC |
| What Do You Meme? | (lookup needed) |
| Exploding Kittens | (lookup needed) |

### Kinfolk Competitors
| Competitor | ASIN |
|-----------|------|
| We're Not Really Strangers | B092GM9NWH |
| TALES Conversation Cards | B0DT3P6M5Q |
| BestSelf Intimacy Deck | B07W1PVNFC |
| TableTopics | (lookup needed) |
| The Skin Deep / The And | (lookup needed) |

## Data Sources
- Amazon.com product pages & search results (web_fetch)
- Brave Search API (when available)
- Sellerboard (for our own BSR/sales data)
- Helium 10 / Jungle Scout (if access added later)

## Improvements Planned
- [ ] Set up Brave Search API key for richer search results
- [ ] Add Helium 10 or Jungle Scout for BSR/revenue estimates
- [ ] Track competitor review velocity week-over-week
- [ ] Add screenshot captures of competitor listings
- [ ] Price history tracking (build simple JSON log)

## File History
| Date | Notes |
|------|-------|
| 2026-02-10 | First report. Brave API unavailable, used direct Amazon scraping. |
