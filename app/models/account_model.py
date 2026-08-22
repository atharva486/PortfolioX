from app.models.base import Base
from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.orm import relationship
class AccountModel(Base):
    __tablename__ = "accounts"
    id  = Column(Integer,primary_key = True) 
    balance = Column(Numeric,nullable=False,default=0.0)

    holdings = relationship("HoldingModel", back_populates="account")

