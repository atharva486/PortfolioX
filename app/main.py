from fastapi import FastAPI,Depends
from app.db.session import get_db
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.api.routes.accounts import router as account_router
from app.api.routes.orders import router as order_router
from app.api.routes.market import router as market_router
app = FastAPI()

app.include_router(account_router)
app.include_router(order_router)
app.include_router(market_router)

@app.get("/health")
def get_root():
    return {"status":"ok"}

@app.get("/db-check")
def db_check(db:Session = Depends(get_db)):

    try:
        result = db.execute(text("SELECT 1")).scalar()
        return {"status": "db_connected", "ping": result}
    except Exception as e:
        return {"status": "db_failed", "error": str(e)}

# if __name__ == "__main__":
#     backend()