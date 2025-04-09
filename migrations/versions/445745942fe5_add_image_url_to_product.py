"""Add image_url to Product

Revision ID: 445745942fe5
Revises: 7530d580f38c
Create Date: 2025-04-08 23:18:11.385113

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '445745942fe5'
down_revision = '7530d580f38c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_url', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.drop_column('image_url')

    # ### end Alembic commands ###
