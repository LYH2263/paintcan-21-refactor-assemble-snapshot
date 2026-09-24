from app.db import connect
from app.engines.assembly import assemble
from app.repositories import openings, rooms, runs, settings
from app.services.snapshot import save_estimate_run


class PaintService:
    """服务入口：只做编排与参数校验，不含公式与落库细节。

    试算组装见 engines.assembly，快照写入见 services.snapshot。
    """
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()

    def list_rooms(self): return rooms.list_all(self._c)

    def room_detail(self, rid):
        r = rooms.get(self._c, rid)
        if not r: return None
        return {"room": r, "openings": openings.for_room(self._c, rid)}

    def settings(self): return settings.get_map(self._c)

    def history(self, limit=50): return runs.list_recent(self._c, limit)

    def get_run(self, run_id):
        """按编号取回一条快照（含钉选的升数），不存在返回 None。"""
        return runs.get(self._c, run_id)

    def estimate(self, room_id, persist, coats=None, coverage=None):
        # 1) 取数：房间与洞口
        detail = self.room_detail(room_id)
        if not detail: return None
        r = detail["room"]

        # 2) 参数解析与校验（设置默认值 + 入参覆盖）
        cov, ct = settings.coverage_coats(self._c)
        cov = float(coverage if coverage is not None else cov)
        ct = int(coats if coats is not None else ct)
        if ct <= 0: raise ValueError("coats must be positive")
        if cov <= 0: raise ValueError("coverage must be positive")

        # 3) 试算组装（纯计算，不写库）
        ops = [{"w": o["w"], "h": o["h"]} for o in detail["openings"]]
        result = assemble(r["length"], r["width"], r["height"], ops, cov, ct)

        # 4) 仅在 persist 为真时写快照；快照钉选值与 result 同源
        run_id = save_estimate_run(self._c, room_id, cov, ct, result) if persist else None
        return {"run_id": run_id, "room_id": room_id, **result}

    def dashboard(self):
        rs = rooms.list_all(self._c)
        return {"room_count": len(rs), "clean": len([x for x in rs if "种子" not in x["name"] and "多种" not in x["name"]]), "dirty": len([x for x in rs if "多种" in x["name"]])}
