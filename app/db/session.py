from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
import os
import dotenv 

dotenv.load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL","sqlite:///portfoliox.db")
engine_args = {}
if "sqlite" in DATABASE_URL:
    engine_args["check_same_thread"] = False

engine = create_engine(
    
    DATABASE_URL, 
    connect_args=engine_args,
    echo=True
)

SessionLocal  = sessionmaker(autocommit = False, autoflush = False, bind = engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    