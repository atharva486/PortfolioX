from sqlalchemy import Column, Integer, String, create_engine, text, text
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine("sqlite:///mydb.db",echo=True)

Base = declarative_base()

class Person(Base):
    __tablename__ = "person"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)

Base.metadata.create_all(engine)


Session =sessionmaker(bind=engine)

with Session() as session:
    new_person = Person(name="John", age=30)
    session.add(new_person)
    session.commit()