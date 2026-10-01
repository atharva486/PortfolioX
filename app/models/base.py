from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Constraint naming convention. Alembic depends on this to emit stable,
# reversible constraint names instead of anonymous ones.
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=naming_convention)


class Base(DeclarativeBase):
    """Typed declarative base.

    Using DeclarativeBase (2.0 style) instead of the untyped
    declarative_base() function means mypy can see every model's
    constructor and column type. Without this, mypy reports bogus
    "unexpected keyword argument" errors on model instantiation.
    """

    metadata = metadata
