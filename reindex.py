from app.database import SessionLocal
from app.models import Payslip, Policy
from app.services.vector_store import index_payslip, index_policy

db = SessionLocal()

for p in db.query(Payslip).all():
    index_payslip(p, p.user.name)
    print(f"Indexed payslip {p.id}")

for pol in db.query(Policy).all():
    index_policy(pol)
    print(f"Indexed policy {pol.id}: {pol.title}")

db.close()
print("Done")
