from app.models.base import Base
from sqlalchemy import Column, Integer, String, Numeric

class AssetModel(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False, unique=True)
    asset_type = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    