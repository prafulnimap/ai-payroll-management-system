from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user, require_hr
from app.models import Payslip, User
from app.schemas import PayslipCreate, PayslipOut, PayslipUpdate
from app.services.vector_store import index_payslip, delete_payslip_vectors
from app.services.cache import invalidate_user

router = APIRouter(prefix="/payslip", tags=["Payslip"])


# ---------- helper functions ----------


def calc_net(gross: Decimal, deductions: Decimal, bonuses: Decimal) -> Decimal:
    net = gross + bonuses - deductions
    if net < 0:
        raise HTTPException(422, "Deductions cannot exceed gross salary plus bonuses")
    return net


def resolve_user_id(current: User, requested_id: int | None) -> int:
    """Decides whose payslip is being accessed, enforcing the access rule."""
    if requested_id is None or requested_id == current.id:
        return current.id
    if current.role != "hr":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "You can only access your own payslips"
        )
    return requested_id


def find_payslip(db: Session, user_id: int, month: int, year: int) -> Payslip:
    payslip = (
        db.query(Payslip)
        .filter(
            Payslip.user_id == user_id, Payslip.month == month, Payslip.year == year
        )
        .first()
    )
    if not payslip:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "No record found for the given period"
        )
    return payslip


# ---------- endpoints ----------


@router.post("/upload", response_model=PayslipOut, status_code=201)
def upload_payslip(
    data: PayslipCreate,
    db: Session = Depends(get_db),
    hr: User = Depends(require_hr),  # HR only
):
    if not db.get(User, data.user_id):
        raise HTTPException(404, "Employee not found")

    exists = (
        db.query(Payslip)
        .filter(
            Payslip.user_id == data.user_id,
            Payslip.month == data.month,
            Payslip.year == data.year,
        )
        .first()
    )
    if exists:
        raise HTTPException(
            409, "Payslip already exists for this period. Use PUT to update it."
        )

    payslip = Payslip(
        **data.model_dump(),
        net_salary=calc_net(data.gross_salary, data.deductions, data.bonuses),
    )
    db.add(payslip)
    db.commit()
    db.refresh(payslip)

    index_payslip(payslip, payslip.user.name)

    invalidate_user(payslip.user_id)
    return payslip


@router.get("/{month}/{year}", response_model=PayslipOut)
def get_payslip(
    month: int = Path(ge=1, le=12),
    year: int = Path(ge=2000, le=2100),
    user_id: int | None = Query(
        default=None, description="HR only: view another employee's payslip"
    ),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    target_id = resolve_user_id(current, user_id)
    return find_payslip(db, target_id, month, year)


@router.put("/{month}/{year}", response_model=PayslipOut)
def update_payslip(
    data: PayslipUpdate,
    user_id: int = Query(description="Employee whose payslip is being corrected"),
    month: int = Path(ge=1, le=12),
    year: int = Path(ge=2000, le=2100),
    db: Session = Depends(get_db),
    hr: User = Depends(require_hr),  # HR only
):
    payslip = find_payslip(db, user_id, month, year)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(payslip, field, value)
    payslip.net_salary = calc_net(
        payslip.gross_salary, payslip.deductions, payslip.bonuses
    )
    db.commit()
    db.refresh(payslip)

    index_payslip(payslip, payslip.user.name)
    invalidate_user(user_id)
    return payslip


@router.delete("/{month}/{year}", status_code=204)
def delete_payslip(
    user_id: int = Query(description="Employee whose payslip is being deleted"),
    month: int = Path(ge=1, le=12),
    year: int = Path(ge=2000, le=2100),
    db: Session = Depends(get_db),
    hr: User = Depends(require_hr),  # HR only
):
    payslip = find_payslip(db, user_id, month, year)
    payslip_id = payslip.id
    db.delete(payslip)
    db.commit()
    delete_payslip_vectors(payslip_id)
    invalidate_user(user_id)
