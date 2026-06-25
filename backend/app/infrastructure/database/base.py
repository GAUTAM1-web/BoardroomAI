from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.infrastructure.database import models as _models  # noqa: E402,F401
