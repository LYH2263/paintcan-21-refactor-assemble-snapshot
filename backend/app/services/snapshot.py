"""快照单元：把试算组装产物写入 calc_runs，并按编号取回核对。

写库只接受 ``assemble_trial`` 的产物，落库的 ``result`` 与对外回包同源、同对象，
因此净面积 / 扣除面积 / 升数天然钉选一致，不在此处二次计算。
"""

import json

from app.repositories import runs
from app.services.trial import PINNED_FIELDS

KIND = "estimate"


def save_snapshot(conn, trial, room_id):
    """persist=True 时调用：钉选组装产物并写入 calc_runs，返回 run id。"""
    return runs.insert(conn, KIND, trial["input"], trial["result"], room_id)


def load_snapshot(conn, run_id):
    """按编号取回一条 calc_runs，解析 input/result JSON；不存在返回 None。"""
    row = runs.get(conn, run_id)
    if row is None:
        return None
    row["input"] = json.loads(row["input_json"])
    row["result"] = json.loads(row["result_json"])
    return row


def snapshot_pinned(snapshot):
    """从取回的快照中提取钉选字段（净面积、扣除面积、升数）。"""
    result = snapshot["result"]
    return {k: result[k] for k in PINNED_FIELDS}
