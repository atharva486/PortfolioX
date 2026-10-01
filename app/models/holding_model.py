from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class HoldingModel(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(ForeignKey("assets.symbol"), nullable=False)

    # Explicit precision. A bare `Column(Numeric)` has NO declared scale,
    # which is unsafe for money and forces Decimal(str(...)) gymnastics
    # at every read. See ADR-012 (financial accuracy).
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    avg_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    account = relationship("AccountModel", back_populates="holdings")
    asset = relationship("AssetModel")

    __table_args__ = (
        UniqueConstraint("account_id", "symbol", name="uq_holding_account_symbol"),
    )
