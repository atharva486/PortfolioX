from abc import ABC,abstractmethod
from decimal import Decimal
from enum import Enum
class AssetType(Enum):
    STOCK = "Stock"
    BOND = "Bond"
class Asset(ABC):

    @property
    @abstractmethod
    def name(self)->str:
        pass
    @property
    @abstractmethod
    def symbol(self)->str:
        pass

    
    @property
    @abstractmethod
    def asset_type(self)->AssetType:
        pass

class Stock(Asset):
    def __init__(self, name:str, symbol:str, sector:str):
        self._name = name
        self._symbol = symbol
        self._sector=sector

    @property
    def name(self)->str:
        return self._name

    @property
    def symbol(self)->str:
        return self._symbol

    @property
    def sector(self)->str:
        return self._sector
    @property
    def asset_type(self)->AssetType:
        return AssetType.STOCK


class Bond(Asset):
    def __init__(self, name:str, symbol:str, coupon_rate:Decimal):
        self._name = name
        self._symbol = symbol
        self._coupon_rate = coupon_rate

    @property
    def name(self)->str:
        return self._name

    @property
    def symbol(self)->str:
        return self._symbol

    @property
    def coupon_rate(self)->Decimal:
        return self._coupon_rate

    @property
    def asset_type(self)->AssetType:
        return AssetType.BOND