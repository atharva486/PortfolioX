from app.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.orm import relationship
class AccountModel(Base):
    __tablename__ = "accounts"
    id  = Column(Integer,primary_key = True) 
    balance: Mapped[Decimal] = mapped_column(Numeric,nullable=False,default=Decimal("0.0"))

    holdings = relationship("HoldingModel", back_populates="account")

