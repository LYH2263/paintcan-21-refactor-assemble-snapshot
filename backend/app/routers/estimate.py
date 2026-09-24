from fastapi import APIRouter, HTTPException
from app.schemas.estimate import EstimateRequest
from app.services.paint_service import PaintService
router = APIRouter()
@router.post("/estimate")
def post_estimate(body: EstimateRequest):
    with PaintService() as s:
        try:
            r = s.estimate(body.room_id, body.persist, body.coats, body.coverage)
        except ValueError as e:
            raise HTTPException(400, str(e))
        if not r: raise HTTPException(404)
        return r
