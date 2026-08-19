from datetime import datetime, timedelta

from app.domain.schemas import Run
from app.storage.db import connect, get_or_create_user, get_runs, save_runs

def make_runs(n=3):
    return [
        Run(
            start_time = datetime(2026, 3, 2, 7, 0) + timedelta(days=2 * i),
            distance_m = 6000 + 500 * i,
            duration_s = 1900 + 120 * i,
        )
        for i in range(n)
    ]

def test_saves_and_reads_back_runs(tmp_path):
    conn = connect(tmp_path / "test.db")
    user_id = get_or_create_user(conn, "jose@example.com")
    save_runs(conn, user_id, make_runs(3))
    assert len(get_runs(conn, user_id)) == 3

def test_duplicate_runs_are_not_inserted_twice(tmp_path):
    conn = connect(tmp_path / "test.db")
    user_id = get_or_create_user(conn, "jose@example.com")
    first = save_runs(conn, user_id, make_runs(3))
    second = save_runs(conn, user_id, make_runs(3))
    assert first == 3
    assert second == 0
    assert len(get_runs(conn, user_id)) == 3

def test_users_do_not_see_each_others_runs(tmp_path):
    conn = connect(tmp_path / "test.db")
    jose = get_or_create_user(conn, "jose@example.com")
    luis = get_or_create_user(conn, "luis@example.com")
    save_runs(conn, jose, make_runs(3))
    save_runs(conn, luis, make_runs(5))
    assert len(get_runs(conn, jose)) == 3
    assert len(get_runs(conn, luis)) == 5

def test_get_or_create_user_is_stable(tmp_path):
    conn = connect(tmp_path / "test.db")
    first = get_or_create_user(conn, "jose@example.com")
    second = get_or_create_user(conn, "jose@example.com")
    assert first == second
