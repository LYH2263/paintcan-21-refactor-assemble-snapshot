"""试算组装单元：把房间与洞口输入装配为净面积 + 升数结果。

纯函数、不触库。组装产物 ``result`` 是对外回包与 calc_runs 快照的**同一权威来源**，
服务层不得在别处重算或改写其中的钉选字段（见 PINNED_FIELDS）。
"""

from app.engines.estimate import estimate_room

# 快照必须与回包钉选一致的字段：净面积、扣除面积（洞口面积）、升数。
PINNED_FIELDS = ("net_m2", "openings_m2", "liters")


def assemble_trial(room, opening_rows, coverage, coats):
    """装配一次试算。

    返回 ``{"input": <落库输入>, "result": <净面积与升数结果>}``；
    ``coverage`` / ``coats`` 须为已解析、已校验的正数。
    """
    cov = float(coverage)
    ct = int(coats)
    ops = [{"w": float(o["w"]), "h": float(o["h"])} for o in opening_rows]
    result = estimate_room(
        float(room["length"]), float(room["width"]), float(room["height"]),
        ops, cov, ct,
    )
    trial_input = {"room_id": room["id"], "coats": ct, "coverage": cov}
    return {"input": trial_input, "result": result}


def pinned_values(result):
    """取出回包/快照需核对一致的钉选数值。"""
    return {k: result[k] for k in PINNED_FIELDS}


def response_body(room_id, result, run_id=None):
    """由同一份 result 拼出对外回包（不复制、不重算钉选字段）。"""
    return {"run_id": run_id, "room_id": room_id, **result}
