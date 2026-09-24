import json, sqlite3
from datetime import datetime, timezone
def insert(conn, kind, payload, result, room_id=None):
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute("INSERT INTO calc_runs(kind,room_id,input_json,result_json,created_at) VALUES (?,?,?,?,?)",
        (kind, room_id, json.dumps(payload, ensure_ascii=False), json.dumps(result, ensure_ascii=False), now))
    conn.commit(); return int(cur.lastrowid)
def list_recent(conn, limit=50):
    return [dict(r) for r in conn.execute("SELECT * FROM calc_runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
def get(conn, run_id):
    """按编号取回一条试算快照，不存在返回 None。"""
    row = conn.execute("SELECT * FROM calc_runs WHERE id=?", (run_id,)).fetchone()
    return dict(row) if row else None
