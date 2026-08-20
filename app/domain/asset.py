from abc import ABC,abstractmethod
from decimal import Decimal
from enum import Enum
class AssetType(Enum):
    STOCK = "Stock"
    BOND = "Bond"
class Asset(ABC):

    @property
    @abstractmethod
    def name(self):
        pass
    @property
    @abstractmethod
    def symbol(self):
        pass
    @property
    @abstractmethod
    def current_price(self):
        pass

    @property
    @abstractmethod
    def asset_type(self)->AssetType:
        pass

class Stock(Asset):
    def __init__(self, name:str, symbol:str, current_price:Decimal, sector:str):
        self._name = name
        self._symbol = symbol
        self._current_price = current_price
        self._sector=sector

    @property
    def name(self):
        return self._name

    @property
    def symbol(self):
        return self._symbol

    @property
    def current_price(self):
        return self._current_price
    @property
    def sector(self):
        return self._sector
    @property
    def asset_type(self):
        return AssetType.STOCK

    @current_price.setter
    def current_price(self, new_price:Decimal):
        if new_price < 0:
            raise ValueError("Price must be a positive value.")
        self._current_price = new_price

class Bond(Asset):
    def __init__(self, name:str, symbol:str, current_price:Decimal, coupon_rate:Decimal):
        self._name = name
        self._symbol = symbol
        self._current_price = current_price
        self._coupon_rate = coupon_rate

    @property
    def name(self):
        return self._name

    @property
    def symbol(self):
        return self._symbol

    @property
    def current_price(self):
        return self._current_price

    @current_price.setter
    def current_price(self, new_price:Decimal):
        if new_price < 0:
            raise ValueError("Price must be a positive value.")
        self._current_price = new_price

    @property
    def coupon_rate(self):
        return self._coupon_rate

    @property
    def asset_type(self):
        return AssetType.BOND