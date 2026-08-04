---
icon: lucide/database
---

# Data Model

SQLite is the system of record for the demo and local runs. The schema lives in
`src/casita/storage.py`.

Key tables:

| Table | Purpose |
| --- | --- |
| `listings` | One row per `(source, source_id)` listing, with normalized facts and enrichment |
| `runs` | Search run history |
| `listing_status` | Funnel status such as contacted, viewing scheduled, passed on |
| `votes` | Up/down preference signal with reviewer reason |
| `actions` | Append-only log for reversible local actions |
| `price_history` | Append-only log of observed asking prices, one row per change |
| `llm_facts` | Cached structured fact extraction |
| `llm_photo_reviews` | Cached Gemini photo review |
| `walk_cache` | Cached walking/driving minutes by rounded coordinates |

## Price History

Rental portals show a snapshot and discard the history, so a unit that has sat
for a month at a cut price looks identical to one listed yesterday. Casita
re-scrapes on every run anyway, so `upsert_run` diffs the incoming price against
the stored row and appends to `price_history` when they differ. The first row
for a listing is its opening price (`prev_price` is null); each later row is a
move. A scrape that repeats the current price writes nothing, and a scrape with
no price at all is treated as "no observation" rather than a drop to zero.

Days on market is derived rather than stored: `last_seen - first_seen`, so
rendering an archived database later doesn't age every listing at once.

The committed fixture predates this table, so it carries no price history —
the days-listed chip shows in the demo, the price-drop badge appears once live
runs accumulate observations.

The committed demo fixture is `fixtures/demo.sqlite`. It keeps enriched listing
facts, photo reviews, and cached route rows. It removes private conversations,
attachments, pending URLs, contact fields, and the chosen home.

## Ways This Could Go Further

The schema could be diagrammed, migrations could be formalized, or the fixture
build could become a checked script. Today, the schema is intentionally close
to the personal tool that produced it.
