import logging
from fastapi import FastAPI
from app.database import Base, engine
from app import models  # noqa: F401
from app.middleware.request_logger import LoggingMiddleware
from app.routers import auth, users, payslip, policy, chat, logs

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Payroll Query System")
app.add_middleware(LoggingMiddleware)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(payslip.router)
app.include_router(policy.router)
app.include_router(chat.router)
app.include_router(logs.router)


@app.get("/")
def health():
    return {"status": "ok"}
