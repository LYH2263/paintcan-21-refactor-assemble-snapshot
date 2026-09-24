"""calc_runs 快照写入步骤（可单独调用）。

负责把一次试算"钉选"成快照并落库：净面积 net_m2、扣除面积
openings_m2、升数 liters 均直接取自组装回包（build_snapshot），
保证库里的快照与返回给调用方的回包同源、同值。

本单元是唯一写 calc_runs 的试算快照入口；persist=False 时
服务层不会调用它，因此试算组装本身绝不写库。
"""
from app.engines.assembly import build_snapshot
from app.repositories import runs

ESTIMATE_KIND = "estimate"


def save_estimate_run(conn, room_id, coverage, coats, result):
    """把试算结果钉选为快照并写入 calc_runs，返回新 run 编号。"""
    payload = {"room_id": room_id, "coats": coats, "coverage": coverage}
    snapshot = build_snapshot(result)
    return runs.insert(conn, ESTIMATE_KIND, payload, snapshot, room_id)
