"""Add AssetModel and normalize HoldingModel

Revision ID: 21c177eefa6c
Revises: 648051be9cd9
Create Date: 2026-08-23 23:35:43.317100

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21c177eefa6c'
down_revision: Union[str, Sequence[str], None] = '648051be9cd9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. CREATE THE ASSETS TABLE FIRST
    op.create_table('assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('asset_type', sa.String(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol')
    )

    # 2. THEN ALTER THE HOLDINGS TABLE
    with op.batch_alter_table('holdings', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_holdings_assets', 'assets', ['symbol'], ['symbol'])
        batch_op.drop_column('asset_type')


def downgrade() -> None:
    """Downgrade schema."""
    # 1. REVERT THE HOLDINGS TABLE FIRST
    with op.batch_alter_table('holdings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('asset_type', sa.VARCHAR(), nullable=False))
        batch_op.drop_constraint('fk_holdings_assets', type_='foreignkey')

    # 2. THEN DROP THE ASSETS TABLE
    op.drop_table('assets')