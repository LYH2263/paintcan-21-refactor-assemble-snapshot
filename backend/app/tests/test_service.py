"""试算组装 / 快照落库 / 按编号取回 的链路测例。

不改动既有引擎数字测例（test_calc.py）。这里通过临时 DATA_DIR 起一套
全新 SQLite，再走 PaintService 编排入口。
"""
import importlib
import json

import pytest

from app.engines.assembly import SNAPSHOT_FIELDS, assemble, build_snapshot
from app.engines.estimate import estimate_room

# 客厅种子：5x4x2.8，门 0.9x2.1、窗 1.5x1.4；coverage=8、2 遍。
LIVING_OPS = [{"w": 0.9, "h": 2.1}, {"w": 1.5, "h": 1.4}]


@pytest.fixture()
def service(tmp_path, monkeypatch):
    # 必须在导入 app.db / app.services 之前指定数据目录。
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    import app.config as config
    import app.db as db
    importlib.reload(config)
    importlib.reload(db)
    import app.seed as seed
    importlib.reload(seed)
    seed.init_db()

    import app.services.paint_service as ps_mod
    importlib.reload(ps_mod)
    import app.services.snapshot as snap_mod
    importlib.reload(snap_mod)
    import app.repositories.runs as runs_mod
    importlib.reload(runs_mod)

    with ps_mod.PaintService() as s:
        yield s


def test_assemble_matches_locked_numbers():
    r = assemble(5, 4, 2.8, LIVING_OPS, 8, 2)
    assert r["gross_m2"] == 50.4
    assert r["openings_m2"] == 3.99
    assert r["net_m2"] == 46.41
    assert r["liters"] == 11.6
    # 与历史入口 estimate_room 完全同口径
    assert r == estimate_room(5, 4, 2.8, LIVING_OPS, 8, 2)


def test_build_snapshot_pins_exact_fields():
    r = assemble(5, 4, 2.8, LIVING_OPS, 8, 2)
    snap = build_snapshot(r)
    assert set(snap) == set(SNAPSHOT_FIELDS) == {"net_m2", "openings_m2", "liters"}
    assert snap == {"net_m2": 46.41, "openings_m2": 3.99, "liters": 11.6}


def _run_count(s):
    return s._c.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]


def test_persist_false_returns_full_response_without_writing(service):
    before = _run_count(service)
    out = service.estimate(1, persist=False)
    # 完整回包
    assert out["run_id"] is None
    assert out["room_id"] == 1
    assert out["net_m2"] == 46.41
    assert out["openings_m2"] == 3.99
    assert out["liters"] == 11.6
    # 未写库
    assert _run_count(service) == before


def test_persist_true_snapshot_matches_response(service):
    before = _run_count(service)
    out = service.estimate(1, persist=True)
    run_id = out["run_id"]
    assert isinstance(run_id, int)
    assert _run_count(service) == before + 1

    row = service.get_run(run_id)
    assert row is not None and row["id"] == run_id
    pinned = json.loads(row["result_json"])
    # 快照钉选值必须与回包一致
    assert pinned["net_m2"] == out["net_m2"] == 46.41
    assert pinned["openings_m2"] == out["openings_m2"] == 3.99
    assert pinned["liters"] == out["liters"] == 11.6
    assert set(pinned) == set(SNAPSHOT_FIELDS)


def test_get_run_by_id_roundtrip(service):
    out = service.estimate(1, persist=True)
    row = service.get_run(out["run_id"])
    assert json.loads(row["result_json"])["liters"] == out["liters"]
    assert service.get_run(999999) is None


def test_invalid_params_rejected(service):
    with pytest.raises(ValueError):
        service.estimate(1, persist=False, coats=0)
    with pytest.raises(ValueError):
        service.estimate(1, persist=False, coverage=0)
