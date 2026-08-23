
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


SQLACHEMY_DATABASE_URL = "sqlite:///./portfoliox.db"

engine = create_engine(
    SQLACHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=True
)

@event.listens_for(engine, "connect", named=True)
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal  = sessionmaker(autocommit = False, autoflush = False, bind = engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    