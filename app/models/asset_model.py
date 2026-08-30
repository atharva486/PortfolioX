from app.models.base import Base
from sqlalchemy import Column, Integer, String, Numeric,CheckConstraint
from app.domain.asset import AssetType

class AssetModel(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False, unique=True)
    asset_type = Column(String, nullable=False)
    sector = Column(String,nullable=True)
    company_name = Column(String, nullable=False)
    coupon_rate = Column(String, nullable=True)

    __table_args__=(
        CheckConstraint(
            f"NOT ( asset_type == '{AssetType.STOCK}' AND sector IS NULL)",
            name = "check_asset_has_sector"
        ),
        CheckConstraint(
            f"NOT ( asset_type == '{AssetType.BOND}' AND coupon_rate IS NULL)",
            name = "check_asset_has_couponRate"
        )
    )

    