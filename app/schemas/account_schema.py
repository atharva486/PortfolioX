from decimal import Decimal

from pydantic import BaseModel, Field


class CreateAccountRequest(BaseModel):
    balance: Decimal = Field(gt=0, description="Initial balance must be positive")


class AccountResponse(BaseModel):
    id: int
    balance: Decimal
    model_config = {"from_attributes": True}
