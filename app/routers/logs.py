from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import require_hr
from app.models import RequestLog, User
from app.schemas import LogOut

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("", response_model=list[LogOut])
def list_logs(
    user_id: int | None = Query(default=None, description="Filter by user"),
    ai_only: bool = Query(
        default=False, description="Only logs that contain an AI response"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    hr: User = Depends(require_hr),
):
    q = db.query(RequestLog)
    if user_id is not None:
        q = q.filter(RequestLog.user_id == user_id)
    if ai_only:
        q = q.filter(RequestLog.ai_response.isnot(None))
    return q.order_by(RequestLog.id.desc()).limit(limit).all()
