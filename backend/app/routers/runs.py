from fastapi import APIRouter, HTTPException
from app.services.paint_service import PaintService

router = APIRouter()


@router.get("/runs/{run_id}")
def get_run(run_id: int):
    """按编号取回一次试算快照，供核对钉选的净面积、扣除面积与升数。"""
    with PaintService() as s:
        snap = s.get_run(run_id)
        if not snap:
            raise HTTPException(404)
        return snap
