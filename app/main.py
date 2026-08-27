from fastapi import FastAPI,Depends
from app.db.session import get_db
from sqlalchemy import text

from sqlalchemy.orm import Session

# Note: Adjust this import path if your file is named something else!
# Assuming your repository is in app/repositories/account_repository.py
from app.repositories.account_repository import AccountRepository
app = FastAPI()

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