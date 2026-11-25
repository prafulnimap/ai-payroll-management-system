from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user, require_hr
from app.models import Policy, User
from app.schemas import PolicyCreate, PolicyOut, PolicyUpdate
from app.services.vector_store import index_policy, delete_policy_vectors
from app.services.cache import clear_all

router = APIRouter(prefix="/policy", tags=["Policy"])


def get_policy_or_404(db: Session, policy_id: int) -> Policy:
    policy = db.get(Policy, policy_id)
    if not policy:
        raise HTTPException(404, "Policy not found")
    return policy


@router.post("", response_model=PolicyOut, status_code=201)
def create_policy(
    data: PolicyCreate, db: Session = Depends(get_db), hr: User = Depends(require_hr)
):
    policy = Policy(**data.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    index_policy(policy)
    clear_all()
    return policy


@router.get("", response_model=list[PolicyOut])
def list_policies(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return db.query(Policy).order_by(Policy.id).all()


@router.get("/{policy_id}", response_model=PolicyOut)
def get_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_policy_or_404(db, policy_id)


@router.put("/{policy_id}", response_model=PolicyOut)
def update_policy(
    policy_id: int,
    data: PolicyUpdate,
    db: Session = Depends(get_db),
    hr: User = Depends(require_hr),
):
    policy = get_policy_or_404(db, policy_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)
    db.commit()
    db.refresh(policy)
    index_policy(policy)
    clear_all()
    return policy


@router.delete("/{policy_id}", status_code=204)
def delete_policy(
    policy_id: int, db: Session = Depends(get_db), hr: User = Depends(require_hr)
):
    policy = get_policy_or_404(db, policy_id)
    db.delete(policy)
    db.commit()
    delete_policy_vectors(policy_id)
    clear_all()
