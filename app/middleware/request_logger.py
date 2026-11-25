import logging
import time

from fastapi import Request
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import SessionLocal
from app.models import RequestLog

logger = logging.getLogger(
    "payroll.access"
)  # This creates or retrieves a Python logger named payroll.access.

SKIP_PATHS = {"/", "/docs", "/redoc", "/openapi.json"}


def write_log(**fields) -> None:
    """Saves one log row. Uses its own DB session. Never lets logging crash a request."""
    db = SessionLocal()
    try:
        db.add(RequestLog(**fields))
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to write request log")
    finally:
        db.close()


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
            state = request.state
            fields = dict(
                user_id=getattr(state, "user_id", None),
                method=request.method,
                endpoint=request.url.path,
                status_code=status_code,
                response_time_ms=elapsed_ms,
                question=getattr(state, "question", None),
                ai_response=getattr(state, "ai_response", None),
            )
            logger.info(
                "%s %s -> %s (%.1f ms) user=%s",
                fields["method"],
                fields["endpoint"],
                status_code,
                elapsed_ms,
                fields["user_id"],
            )
            await run_in_threadpool(write_log, **fields)


# Import	            Purpose
# logging	            Writes application log messages to the console or configured logging destination.
# time	                Measures how long a request takes.
# Request	            Gives us access to information about the incoming HTTP request.
# run_in_threadpool	    Runs blocking database work in a worker thread.
# BaseHTTPMiddleware	Base class used to create HTTP middleware.
# SessionLocal	        Creates a SQLAlchemy database session.
# RequestLog	        The SQLAlchemy model representing our logs table.

# What each part does:

# SKIP_PATHS: the docs pages are noise, so we don’t log them.
# time.perf_counter(): a high-precision timer. We measure before and after call_next, which is the actual endpoint.
# try/finally: the log is written whether the request succeeded or crashed with an error. Failed requests are the ones you most want recorded.
# getattr(state, "user_id", None): reads what the endpoint stored. If nothing was stored (for example, a 401), it falls back to None.
# write_log has its own try/except. If the database write fails, the user’s request still succeeds, because observability should never break the product.
# run_in_threadpool: the DB write is blocking, and middleware is async. Running it in a thread keeps the server responsive.
# We never log request bodies or headers, so passwords and tokens can’t leak into the logs. The only body content stored is the chat question
