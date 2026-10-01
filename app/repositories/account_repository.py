from decimal import Decimal
from typing import cast

from sqlalchemy.orm import Session

from app.domain.account import Account, Position
from app.domain.asset import Bond, Stock
from app.models.account_model import AccountModel
from app.models.asset_model import AssetModel
from app.models.holding_model import HoldingModel


class AccountRepository:
    def __init__(self, session: Session):
        self.session = session

    def stock_or_bond(self, asset: AssetModel) -> Stock | Bond:
        asset_type = cast(str, asset.asset_type)
        if asset_type == "BOND":
            return Bond(
                symbol=cast(str, asset.symbol),
                name=cast(str, asset.company_name),
                coupon_rate=cast(Decimal, asset.coupon_rate),
            )
        else:
            return Stock(
                symbol=cast(str, asset.symbol),
                name=cast(str, asset.company_name),
                sector=cast(str, asset.sector),
            )

    def create_account(self, balance: Decimal) -> AccountModel:
        account_db = AccountModel(balance=balance)
        self.session.add(account_db)
        self.session.commit()
        self.session.refresh(account_db)
        return account_db

    def get_account(
        self, account_id: int, for_update: bool = False
    ) -> AccountModel | None:
        """Fetch an account row, or None if it does not exist.

        `for_update=True` acquires a PostgreSQL row-level lock
        (SELECT ... FOR UPDATE) per ADR-009. It is opt-in: reads should
        not silently take write locks. Always re-check funds inside the
        same transaction if you use it.
        """
        query = self.session.query(AccountModel).filter(AccountModel.id == account_id)
        if for_update:
            query = query.with_for_update()
        return query.first()

    def get_all_accounts(self) -> list[AccountModel]:
        return self.session.query(AccountModel).all()

    def _to_domain(self, account: AccountModel | None) -> Account | None:
        if account is None:
            return None

        domain_account = Account(balance=Decimal(str(account.balance)), id=account.id)
        holdings: dict[str, Position] = {}
        for holding in account.holdings:
            holdings[holding.symbol] = Position(
                quantity=holding.quantity,
                avg_price=Decimal(str(holding.avg_price)),
                asset=self.stock_or_bond(holding.asset),
            )
        domain_account.holdings = holdings
        return domain_account

    def get_domain_account(self, account_id: int) -> Account | None:
        raw_account = self.get_account(account_id=account_id)
        return self._to_domain(account=raw_account)

    def save(self, domain_account: Account) -> None:
        """Persist a domain Account back to the database.

        `for_update=True` is deliberate: we are about to mutate the
        balance, so we must hold the row lock (ADR-009) for the duration
        of the write, following the account-before-holdings lock order
        (ADR-010).
        """
        account = self.get_account(domain_account.id, for_update=True)
        if account is None:
            return
        account.balance = domain_account.balance

        # Track what symbols currently exist in the domain model
        domain_symbols = set(domain_account.holdings.keys())

        # Load all existing holding rows from the database for this account
        existing_holdings = (
            self.session.query(HoldingModel)
            .filter(HoldingModel.account_id == domain_account.id)
            .all()
        )

        # Create a dictionary for fast lookup of existing database holdings
        existing_holdings_dict = {h.symbol: h for h in existing_holdings}

        # 1. Update existing rows or insert new ones
        for symbol, holding in domain_account.holdings.items():
            if symbol in existing_holdings_dict:
                # Update existing holding
                existing_holdings_dict[symbol].quantity = holding.quantity
                existing_holdings_dict[symbol].avg_price = holding.avg_price
            else:
                # Insert new holding
                new_holding = HoldingModel(
                    account_id=domain_account.id,
                    symbol=symbol,
                    quantity=holding.quantity,
                    avg_price=holding.avg_price,
                )
                self.session.add(new_holding)

        # 2. Delete any database holding rows that are NO LONGER in the domain model
        # (This happens when we sell all shares and the quantity drops to 0)
        for symbol, holding_model in existing_holdings_dict.items():
            if symbol not in domain_symbols:
                self.session.delete(holding_model)

        self.session.commit()
