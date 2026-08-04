"""Price history: the log, the badge, and the days-listed chip.

Rental portals throw price history away, so the only copy we get is the one
`upsert_run` writes by diffing each scrape against the stored row. These tests
pin that diffing behavior — especially the cases that should write *nothing*,
since a spurious row shows a fake price drop to the reviewer.
"""
from datetime import datetime, timedelta

from casita import html, storage
from casita.models import Listing


def _listing(price: int | None, key: str = "1") -> Listing:
    return Listing(
        source="craigslist", source_id=key,
        url=f"https://example.test/{key}", price=price,
        beds=3, baths=2, dog_policy="large_ok", llm_severity="ok",
    )


def _connect(tmp_path, monkeypatch):
    monkeypatch.setenv("CASITA_DB_PATH", str(tmp_path / "test.sqlite"))
    return storage.connect()


def test_first_scrape_records_opening_price_with_no_previous(tmp_path, monkeypatch):
    with _connect(tmp_path, monkeypatch) as conn:
        storage.upsert_run(conn, [_listing(5200)], succeeded_sources=["craigslist"])
        rows = storage.price_history_for(conn, "craigslist:1")

    assert len(rows) == 1
    assert rows[0]["price"] == 5200
    assert rows[0]["prev_price"] is None


def test_price_drop_records_change_with_previous_price(tmp_path, monkeypatch):
    with _connect(tmp_path, monkeypatch) as conn:
        storage.upsert_run(conn, [_listing(5200)], succeeded_sources=["craigslist"])
        storage.upsert_run(conn, [_listing(4950)], succeeded_sources=["craigslist"])
        rows = storage.price_history_for(conn, "craigslist:1")
        changes = storage.price_changes(conn)

    assert [(r["price"], r["prev_price"]) for r in rows] == [(5200, None), (4950, 5200)]
    assert changes["craigslist:1"]["price"] == 4950
    assert changes["craigslist:1"]["prev_price"] == 5200


def test_unchanged_price_records_nothing_on_rescrape(tmp_path, monkeypatch):
    with _connect(tmp_path, monkeypatch) as conn:
        for _ in range(3):
            storage.upsert_run(conn, [_listing(5200)], succeeded_sources=["craigslist"])
        rows = storage.price_history_for(conn, "craigslist:1")

    assert len(rows) == 1


def test_null_price_scrape_records_nothing_and_keeps_stored_price(tmp_path, monkeypatch):
    # A search-results re-scrape without a price coalesces to the stored value;
    # logging it would read as a drop to $0.
    with _connect(tmp_path, monkeypatch) as conn:
        storage.upsert_run(conn, [_listing(5200)], succeeded_sources=["craigslist"])
        storage.upsert_run(conn, [_listing(None)], succeeded_sources=["craigslist"])
        rows = storage.price_history_for(conn, "craigslist:1")
        price = conn.execute(
            "SELECT price FROM listings WHERE key=?", ("craigslist:1",)
        ).fetchone()["price"]

    assert len(rows) == 1
    assert price == 5200


def test_opening_price_only_excluded_from_price_changes(tmp_path, monkeypatch):
    with _connect(tmp_path, monkeypatch) as conn:
        storage.upsert_run(conn, [_listing(5200)], succeeded_sources=["craigslist"])
        changes = storage.price_changes(conn)

    assert changes == {}


def test_price_drop_renders_accented_pill_with_delta():
    rendered = html.price_change_html({"price": 4950, "prev_price": 5200})

    assert "price-change is-drop" in rendered
    assert "↓ $250" in rendered
    assert "was $5,200/mo" in rendered


def test_price_rise_renders_muted_pill_with_delta():
    rendered = html.price_change_html({"price": 5400, "prev_price": 5200})

    assert "price-change is-rise" in rendered
    assert "↑ $200" in rendered


def test_no_previous_price_renders_no_pill():
    assert html.price_change_html({"price": 5200, "prev_price": None}) == ""
    assert html.price_change_html(None) == ""


def test_price_drop_map_renders_pill_on_card():
    L = _listing(4950)
    change = {"price": 4950, "prev_price": 5200}

    rendered = html.render([L], price_change_map={L.key: change})

    assert "↓ $250" in rendered
    assert "1</span><span class=\"stat-label\">price drop" in rendered


def test_listing_without_change_renders_no_pill_on_card():
    # The class name also appears in the inlined CSS, so match the element.
    rendered = html.render([_listing(4950)])

    assert 'class="price-change' not in rendered


def _seen_for(days: int) -> Listing:
    L = _listing(5200)
    L.first_seen = datetime(2026, 6, 1)
    L.last_seen = L.first_seen + timedelta(days=days)
    return L


def test_long_listed_days_render_stale_chip():
    assert "31 days listed" in html._card(_seen_for(31))


def test_recently_listed_days_render_no_chip():
    assert "days listed" not in html._card(_seen_for(3))


def test_missing_first_seen_renders_no_chip():
    assert html.days_listed(_listing(5200)) is None
    assert "days listed" not in html._card(_listing(5200))


def test_days_listed_measured_from_last_seen_not_today():
    # An archived DB rendered months later must not age every listing.
    assert html.days_listed(_seen_for(9)) == 9


def test_missing_last_seen_falls_back_to_zero_days():
    L = _listing(5200)
    L.first_seen = datetime(2026, 6, 1)

    assert html.days_listed(L) == 0
