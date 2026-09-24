"""试算组装 / 快照 / 服务编排的行为测例。

不依赖 pytest fixture，故在无 pytest 的环境也可用
``python3 -m app.tests.test_trial_snapshot`` 直接跑。
"""

import sqlite3

import app.services.paint_service as paint_service
from app.services import snapshot as snapshot_svc
from app.services.trial import assemble_trial, pinned_values, response_body

LIVING_ROOM = {"id": 1, "name": "客厅", "length": 5.0, "width": 4.0, "height": 2.8}
LIVING_OPENINGS = [{"w": 0.9, "h": 2.1}, {"w": 1.5, "h": 1.4}]

SCHEMA = """
CREATE TABLE rooms(id INTEGER PRIMARY KEY, name TEXT, length REAL, width REAL, height REAL);
CREATE TABLE openings(id INTEGER PRIMARY KEY, room_id INTEGER, kind TEXT, w REAL, h REAL);
CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE calc_runs(id INTEGER PRIMARY KEY, kind TEXT, room_id INTEGER, input_json TEXT, result_json TEXT, created_at TEXT);
"""


def _build_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.execute("INSERT INTO rooms(name,length,width,height) VALUES ('客厅',5.0,4.0,2.8)")
    conn.execute("INSERT INTO openings(room_id,kind,w,h) VALUES (1,'door',0.9,2.1)")
    conn.execute("INSERT INTO openings(room_id,kind,w,h) VALUES (1,'window',1.5,1.4)")
    conn.execute("INSERT INTO settings(key,value) VALUES ('coverage','8')")
    conn.execute("INSERT INTO settings(key,value) VALUES ('coats','2')")
    conn.commit()
    return conn


def _count_runs(conn):
    return conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]


def test_assemble_pins_living_room_numbers():
    trial = assemble_trial(LIVING_ROOM, LIVING_OPENINGS, 8, 2)
    # 既有测例锁定的口径：净 46.41、扣除 3.99、升数 11.6。
    assert pinned_values(trial["result"]) == {
        "net_m2": 46.41, "openings_m2": 3.99, "liters": 11.6,
    }
    assert trial["input"] == {"room_id": 1, "coats": 2, "coverage": 8.0}


def test_snapshot_pinned_matches_response():
    conn = _build_conn()
    trial = assemble_trial(LIVING_ROOM, LIVING_OPENINGS, 8, 2)
    run_id = snapshot_svc.save_snapshot(conn, trial, 1)
    snap = snapshot_svc.load_snapshot(conn, run_id)
    # 快照取回的钉选字段必须与组装/回包同源一致。
    assert snapshot_svc.snapshot_pinned(snap) == pinned_values(trial["result"])
    body = response_body(1, trial["result"], run_id)
    assert body["run_id"] == run_id
    assert body["net_m2"] == snap["result"]["net_m2"]
    assert body["openings_m2"] == snap["result"]["openings_m2"]
    assert body["liters"] == snap["result"]["liters"]
    conn.close()


def test_get_run_by_id_returns_locked_liters():
    conn = _build_conn()
    original_connect = paint_service.connect
    paint_service.connect = lambda: conn
    try:
        s = paint_service.PaintService()
        body = s.estimate(1, True)
        fetched = s.get_run(body["run_id"])
        assert fetched is not None
        assert fetched["id"] == body["run_id"]
        assert fetched["result"]["liters"] == 11.6
        assert s.get_run(99999) is None
        s.close()
    finally:
        paint_service.connect = original_connect


def test_persist_false_returns_full_body_without_writing():
    conn = _build_conn()
    original_connect = paint_service.connect
    paint_service.connect = lambda: conn
    try:
        s = paint_service.PaintService()
        before = _count_runs(conn)
        body = s.estimate(1, False)
        after = _count_runs(conn)
        assert after == before  # 试算不写库
        assert body["run_id"] is None
        # 完整回包仍可用于前端展示。
        assert body["net_m2"] == 46.41
        assert body["openings_m2"] == 3.99
        assert body["liters"] == 11.6
        assert body["coats"] == 2
        persisted = s.estimate(1, True)
        assert _count_runs(conn) == before + 1  # persist=True 才落一条
        assert persisted["run_id"] is not None
        s.close()
    finally:
        paint_service.connect = original_connect


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("ok", fn.__name__)
    print(f"{len(fns)} passed")


if __name__ == "__main__":
    _run_all()
