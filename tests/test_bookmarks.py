"""Bookmarks: the saved-for-later flag, its CLI verb, and undo.

The table is keyed on (listing_key, voter), so the interesting behavior is all
about two reviewers not stepping on each other, and about the verb being safe
to repeat. Rendering is covered only far enough to pin the attribute the card
button reads.
"""
import pytest
from click.testing import CliRunner

import casita
from casita import html, storage
from casita.models import Listing


KEY = "craigslist:1"


@pytest.fixture
def db(tmp_path, monkeypatch):
    """A DB with one listing to bookmark."""
    monkeypatch.setenv("CASITA_DB_PATH", str(tmp_path / "test.sqlite"))
    L = Listing(
        source="craigslist", source_id="1", url="https://example.test/1",
        price=5200, beds=3, baths=2, dog_policy="large_ok", llm_severity="ok",
    )
    with storage.connect() as conn:
        storage.upsert_run(conn, [L], succeeded_sources=["craigslist"])
    return tmp_path


def _run(*args):
    return CliRunner().invoke(casita.cli, [*args, "--local"])


def test_no_bookmarks_returns_empty_set(db):
    with storage.connect() as conn:
        assert storage.bookmarked_keys(conn) == set()


def test_bookmark_command_marks_listing_saved(db):
    result = _run("bookmark", "--listing", KEY)

    assert result.exit_code == 0
    with storage.connect() as conn:
        assert storage.bookmarked_keys(conn) == {KEY}


def test_repeated_bookmark_by_same_voter_keeps_one_row(db):
    _run("bookmark", "--listing", KEY, "--voter", "reviewer_a")
    _run("bookmark", "--listing", KEY, "--voter", "reviewer_a")

    with storage.connect() as conn:
        rows = conn.execute("SELECT * FROM bookmarks").fetchall()
    assert len(rows) == 1


def test_remove_by_one_voter_keeps_the_other_voters_bookmark(db):
    _run("bookmark", "--listing", KEY, "--voter", "reviewer_a")
    _run("bookmark", "--listing", KEY, "--voter", "reviewer_b")

    _run("bookmark", "--listing", KEY, "--voter", "reviewer_a", "--remove")

    with storage.connect() as conn:
        # Still bookmarked — reviewer_b never let go of it.
        assert storage.bookmarked_keys(conn) == {KEY}
        voters = [r[0] for r in conn.execute("SELECT voter FROM bookmarks")]
    assert voters == ["reviewer_b"]


def test_remove_by_last_voter_clears_the_bookmark(db):
    _run("bookmark", "--listing", KEY, "--voter", "reviewer_a")

    _run("bookmark", "--listing", KEY, "--voter", "reviewer_a", "--remove")

    with storage.connect() as conn:
        assert storage.bookmarked_keys(conn) == set()


def test_bookmark_unknown_listing_exits_nonzero(db):
    result = _run("bookmark", "--listing", "zillow:does-not-exist")

    assert result.exit_code == 1
    with storage.connect() as conn:
        assert storage.bookmarked_keys(conn) == set()


def test_undo_after_bookmark_removes_it(db):
    _run("bookmark", "--listing", KEY, "--voter", "reviewer_a")

    _run("undo", "--listing", KEY, "--voter", "reviewer_a")

    with storage.connect() as conn:
        assert storage.bookmarked_keys(conn) == set()


def test_undo_after_remove_restores_it(db):
    _run("bookmark", "--listing", KEY, "--voter", "reviewer_a")
    _run("bookmark", "--listing", KEY, "--voter", "reviewer_a", "--remove")

    _run("undo", "--listing", KEY, "--voter", "reviewer_a")

    with storage.connect() as conn:
        assert storage.bookmarked_keys(conn) == {KEY}


def test_bookmarked_listing_renders_pressed_button(db):
    L = Listing(source="craigslist", source_id="1", url="https://example.test/1",
                price=5200, dog_policy="large_ok", llm_severity="ok")

    assert 'data-bookmarked="true"' in html._card(L, bookmarked=True)
    assert 'data-bookmarked="false"' in html._card(L, bookmarked=False)
