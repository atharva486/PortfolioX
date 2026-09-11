from fastapi import FastAPI,Depends
from app.db.session import get_db
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.api.routes.accounts import router as account_router
from app.api.routes.orders import router as order_router
from app.api.routes.market import router as market_router
from app.api.routes.portfolio import router as portfolio_router
from app.api.routes.ai import router as ai_router
app = FastAPI()

app.include_router(account_router)
app.include_router(order_router)
app.include_router(market_router)
app.include_router(portfolio_router)
app.include_router(ai_router)

# if __name__ == "__main__":
#     backend()