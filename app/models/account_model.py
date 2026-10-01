from decimal import Decimal

from sqlalchemy import Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.holding_model import HoldingModel


class AccountModel(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Explicit precision. A bare `Numeric` has NO declared scale, which is
    # unsafe for money and is the reason the codebase needed
    # Decimal(str(...)) at every read site. See ADR-001.
    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("0.0")
    )

    holdings: Mapped[list["HoldingModel"]] = relationship(
        "HoldingModel", back_populates="account"
    )
