from decimal import Decimal
from cryptography.fernet import Fernet
from sqlalchemy.types import String, TypeDecorator
from app.config import settings

fernet = Fernet(settings.ENCRYPTION_KEY)


class EncryptedMoney(TypeDecorator):
    """Encrypts on the way into the database, decrypts on the way out."""

    impl = String(255)
    cache_ok = True

    def process_bind_param(self, value, dialect):  # Python -> database
        if value is None:
            return None
        value = Decimal(value).quantize(Decimal("0.01"))  # always 2 decimal places
        return fernet.encrypt(str(value).encode()).decode()

    def process_result_value(self, value, dialect):  # database -> Python
        if value is None:
            return None
        return Decimal(fernet.decrypt(value.encode()).decode())
