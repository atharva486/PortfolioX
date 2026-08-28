from fastapi import APIRouter,Depends,HTTPException
from app.db.session import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.account_schema import CreateAccountRequest,AccountResponse
from app.repositories.account_repository import AccountRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.order_schema import OrderCreate,OrderResponse
from app.domain.exceptions import InsufficientFundsError, InsufficientHoldingsError

router = APIRouter(tags=["Orders"])
@router.post('/accounts/{account_id}/orders', response_model=OrderResponse)
def place_order_endpoint(account_id: int, order_in: OrderCreate, db: Session = Depends(get_db)):
    order_repo = OrderRepository(db)
    
    try:
        result = order_repo.place_order(
            live_price=order_in.live_price,
            symbol=order_in.symbol,
            account_id=account_id,
            order_side=order_in.side,
            limit_price=order_in.limit_price,
            order_type=order_in.order_type,
            quantity=order_in.quantity
        )
        
        if result is None:
            raise HTTPException(status_code=404, detail="Account or Asset not found")
            
        return result
        
    except (InsufficientFundsError, InsufficientHoldingsError) as e:
        # Catch domain rules breaking and turn them into a clean 400 error!
        raise HTTPException(status_code=400, detail=str(e))