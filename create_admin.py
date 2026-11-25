from app.database import SessionLocal, Base, engine
from app import models  # noqa: F401
from app.models import User
from app.security import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()

if not db.query(User).filter(User.email == "hr@company.com").first():
    db.add(User(
        name="HR Admin",
        email="hr@company.com",
        password_hash=hash_password("hr12345678"),
        role="hr",
    ))
    db.commit()
    print("HR user created: hr@company.com / hr12345678")
else:
    print("HR user already exists")

db.close()