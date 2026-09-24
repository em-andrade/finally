from __future__ import annotations

from app.db import get_snapshots, record_snapshot


def test_record_snapshot_returns_row(initialized_db):
    snap = record_snapshot(10500.0)
    assert snap["total_value"] == 10500.0
    assert snap["id"]
    assert snap["recorded_at"]


def test_get_snapshots_chronological_order(initialized_db):
    first = record_snapshot(10000.0)
    second = record_snapshot(10250.0)
    snaps = get_snapshots()
    assert [s["id"] for s in snaps] == [first["id"], second["id"]]


def test_get_snapshots_since_filter(initialized_db):
    record_snapshot(10000.0)
    cutoff = record_snapshot(10100.0)["recorded_at"]
    record_snapshot(10200.0)
    snaps = get_snapshots(since=cutoff)
    assert all(s["recorded_at"] >= cutoff for s in snaps)
    assert len(snaps) == 2


def test_snapshots_scoped_per_user(initialized_db):
    record_snapshot(10000.0, user_id="someone-else")
    assert get_snapshots() == []
    assert len(get_snapshots(user_id="someone-else")) == 1
