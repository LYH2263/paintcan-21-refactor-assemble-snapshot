from fastapi import APIRouter, HTTPException
from app.services.paint_service import PaintService
router = APIRouter()
@router.get("/history")
def history(limit: int = 50):
    with PaintService() as s: return {"items": s.history(limit)}
@router.get("/history/{run_id}")
def get_run(run_id: int):
    """按编号取回一次试算快照，用于核对钉选的净面积/扣除面积/升数。"""
    with PaintService() as s:
        row = s.get_run(run_id)
        if not row: raise HTTPException(404)
        return row
