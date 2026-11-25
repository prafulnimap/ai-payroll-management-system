from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    String,
    Integer,
    Numeric,
    ForeignKey,
    DateTime,
    Text,
    UniqueConstraint,
    Float,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.crypto import EncryptedMoney


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        String(20), default="employee"
    )  # "employee" or "hr"

    payslips: Mapped[list["Payslip"]] = relationship(back_populates="user")


class Payslip(Base):
    __tablename__ = "payslips"
    __table_args__ = (UniqueConstraint("user_id", "month", "year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    month: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    gross_salary: Mapped[Decimal] = mapped_column(EncryptedMoney)
    deductions: Mapped[Decimal] = mapped_column(EncryptedMoney, default=Decimal("0"))
    net_salary: Mapped[Decimal] = mapped_column(EncryptedMoney)
    bonuses: Mapped[Decimal] = mapped_column(EncryptedMoney, default=Decimal("0"))
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user: Mapped["User"] = relationship(back_populates="payslips")


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class RequestLog(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    method: Mapped[str] = mapped_column(String(10))
    endpoint: Mapped[str] = mapped_column(String(300))
    status_code: Mapped[int] = mapped_column(Integer)
    response_time_ms: Mapped[float] = mapped_column(Float)
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_response: Mapped[str | None] = mapped_column(Text, nullable=True)
