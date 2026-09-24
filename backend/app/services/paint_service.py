from app.db import connect
from app.repositories import openings, rooms, runs, settings
from app.services import snapshot as snapshot_svc
from app.services.trial import assemble_trial, response_body

class PaintService:
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
    def get_run(self, run_id): return snapshot_svc.load_snapshot(self._c, run_id)

    def estimate(self, room_id, persist, coats=None, coverage=None):
        # 编排：取数 -> 校验/解析参数 -> 组装试算 ->（按需）快照 -> 回包。
        detail = self.room_detail(room_id)
        if not detail: return None
        cov, ct = settings.coverage_coats(self._c)
        cov = float(coverage or cov)
        ct = int(coats or ct)
        if cov <= 0 or ct <= 0:
            raise ValueError("coverage and coats must be positive")

        trial = assemble_trial(detail["room"], detail["openings"], cov, ct)
        # persist=False：返回完整回包但绝不写库；persist=True：快照钉选同一份 result。
        run_id = snapshot_svc.save_snapshot(self._c, trial, room_id) if persist else None
        return response_body(room_id, trial["result"], run_id)

    def dashboard(self):
        rs = rooms.list_all(self._c)
        return {"room_count": len(rs), "clean": len([x for x in rs if "种子" not in x["name"] and "多种" not in x["name"]]), "dirty": len([x for x in rs if "多种" in x["name"]])}
