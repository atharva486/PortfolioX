from pydantic import BaseModel,Field
from decimal import Decimal

class createAccount(BaseModel):
    balance:Decimal=Field(gt=0,description="Initial balance must be positive")

class AcccountResponse(BaseModel):
    id:int
    balance:Decimal
    

