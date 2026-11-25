from pydantic import BaseModel, EmailStr, Field
from decimal import Decimal
from datetime import datetime
from typing import Annotated


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# A reusable type: non-negative money with max 2 decimal places
Money = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]


class PayslipCreate(BaseModel):
    user_id: int
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)
    gross_salary: Money
    deductions: Money = Decimal("0")
    bonuses: Money = Decimal("0")
    pdf_url: str | None = Field(default=None, max_length=500)


class PayslipUpdate(BaseModel):
    gross_salary: Money | None = None
    deductions: Money | None = None
    bonuses: Money | None = None
    pdf_url: str | None = Field(default=None, max_length=500)


class PayslipOut(BaseModel):
    id: int
    user_id: int
    month: int
    year: int
    gross_salary: Decimal
    deductions: Decimal
    net_salary: Decimal
    bonuses: Decimal
    pdf_url: str | None
    model_config = {"from_attributes": True}


class PolicyCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=10)


class PolicyUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    content: str | None = Field(default=None, min_length=10)


class PolicyOut(BaseModel):
    id: int
    title: str
    content: str
    updated_at: datetime
    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    cached: bool = False


class LogOut(BaseModel):
    id: int
    timestamp: datetime
    user_id: int | None
    method: str
    endpoint: str
    status_code: int
    response_time_ms: float
    question: str | None
    ai_response: str | None
    model_config = {"from_attributes": True}
