from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session


from app.database.db import get_db
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

router = APIRouter()

@router.get("/", status_code=status.HTTP_200_OK)
def healthcheck(db: Session = Depends(get_db)):
    """
    Health Check Endpoint
    Checks database connectivity and returns status.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except SQLAlchemyError:
        return Response(content='{"status": "error", "database": "disconnected"}', media_type="application/json", status_code=503)
