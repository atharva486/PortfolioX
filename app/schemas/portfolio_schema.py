from pydantic import BaseModel
from decimal import Decimal
from app.schemas.account_schema import AccountResponse

class HoldingSchema(BaseModel):
    symbol:str
    quantity:int    
    avg_price:Decimal
    live_price:Decimal|None =None
    

class PortfolioSummaryResponse(BaseModel):
    holdings:list[HoldingSchema]
    total_value:Decimal|None =None
    total_pnl:Decimal|None =None
    account:AccountResponse
    model_config={"from_attributes":True}

    
    
    
