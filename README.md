# Casita

[![Documentation](https://img.shields.io/badge/docs-casita-0b6e4f?style=for-the-badge)](https://matin.github.io/casita/)

Casita is a personal rental-search tool published as a public repo.

It started as a small script for a time-boxed San Francisco rental search with
two large dogs: scrape Zillow, Craigslist, Zumper, and Redfin; enrich the
listings; rank them; and render a static page that was easier to review than
four open browser tabs.

This is not a product or service. It is published as-is, under MIT, as a
personal-use codebase for an interview loop. The interesting part is what a
candidate chooses to improve.

## My changes:

### Changes for the User Experience on Website:

1) **Added a jump-to-top button:** I noticed that the website did not have any jump-to-top button, meaning if a user scrolled down quite a lot but then wanted to come back up and change something in their query, they would have to scroll all the way back up. So, I added this feature to improve, or at least ease, the user experience. I just added a button that listens to scroll, and it shows up when one page-view has been scrolled by.

2) **Bookmark for entries:** I added a bookmark button on the listing cards for users to save listings that they like for them to peruse later. I also added a "Bookmarked" button, which when clicked, would show us only the bookmarked listings, and when unclicked, would show all listings. This way, I had to create no new page to do this action. Since the browser cannot access the SQL directly, I needed a real write path for the bookmarks. I saved the click state to local storage and added a new Bookmarks table in SQLite where they were stored. I added a test suite for this.

3) **Sorting the listings:** When I immediately googled "cheap apartments in Bay Area" upon seeing the pricings on the demo listing, I got the idea to add "Sort" according to price on the website so that other users can also check according to their preferences and budget. The sorting was all client-side and I made no backend changes in it. 

4) **Fix automatic scroll-up:** I noticed that when we click "Back to All Listings" after clicking on a listing card and seeing its details, the page jumps back up to the top. If this persists, then every time a user will click out of a listing, they would be thrown back to the top, which could make it a frustrating experience for them to browse. Now, even if we click "Back to All Listings", we stay at the same level where user had clicked the listing from.

### Addition in Functionality (that would work on the scraped data):

1) **Added Price-History:** The demo right now is a convenient and better way to view very personalized and specific listings from different websites like Zillow and Craigslist in one place, but I wanted to add one more feature that would elevate it from Zillow. I added a feature that would display how long ago the listing was published and how much its price has fallen since then. This feature would help users get a better idea of how the property that they are viewing is doing, and they will be able to make better decisions. I added tests for this. I also moved the "Added" filter to make the UI look less cluttered.

We cannot really view the price-change in the demo because the data is static, so I seeded the tables with test data to confirm that it works. How long it has been since the listing was uploaded still shows with static data. If you want to view everything with the original sqlite file, you can use it, but price history won't be visible. If you use the same sqlite file that I have in my project as is, you will see my price history feature as well, which will work with scraped data.

### Scope:
If given more time, I would like to make sure that my features sit even more harmoniously on the web page.

## Demo

The demo is credentials-free and uses a sanitized SQLite fixture with cached
route times and precomputed LLM enrichment.

```bash
uv sync
uv run playwright install chromium
uv run casita demo
```

Then open <http://127.0.0.1:8765/>.

The demo does not scrape, call Vertex, deploy to Firebase, read GCS, or call the
Google Maps Routes API. It does use Playwright's local Chromium browser to
render Open Graph preview images from listing photos and facts. Live `search` /
`enrich` / `publish` paths still exist for private use and are controlled by
environment variables; see `.env.example`.

## What It Does

- Scrapes active rental listings from Zillow, Craigslist, Zumper, and Redfin.
- Normalizes listing facts into SQLite.
- Classifies dog policy and enriches details from listing pages.
- Uses Gemini for fact extraction, photo review, share blurbs, and ranking.
- Computes walking and driving times to curated SF / Marin anchors.
- Renders a static, mobile-friendly site with index and detail pages.
- Records votes and passes so future ranking can learn from reviewer feedback.

The domain assumptions are intentionally personal: large dogs, San Francisco
walkability, Marin driving context, trails, beaches, and good bakeries nearby.
That is the point of a personal tool.

## Docs

The [documentation site](https://matin.github.io/casita/) explains the systems
without turning them into assigned tasks. To run it locally instead:

```bash
uv run zensical serve
```

Start at `docs/index.md`, or run `uv run zensical build` to generate the site.

## Checks

```bash
make check
```

This compiles the Python modules, runs the pytest suite, runs the public leak
validator, builds the docs, builds the Python package artifacts, and checks
that the CLI imports.

## Contributing

Read `CONTRIBUTING.md`. The short version: fork the repo, pick something you
think makes Casita better, and explain why you chose it.
