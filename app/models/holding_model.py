from app.models.base import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Numeric
from sqlalchemy.orm import relationship

class HoldingModel(Base):
    __tablename__ = "holdings"
    id = Column(Integer, primary_key = True)
    account_id  = Column(Integer,ForeignKey("accounts.id"),nullable=False )
    symbol = Column(String,ForeignKey("assets.symbol"),nullable=False)
    quantity = Column(Numeric,nullable=False)
    avg_price = Column(Numeric,nullable=False)

    account = relationship("AccountModel", back_populates="holdings")
    asset = relationship("AssetModel")