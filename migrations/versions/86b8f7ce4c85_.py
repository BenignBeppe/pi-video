"""empty message

Revision ID: 86b8f7ce4c85
Revises: f2363b28258c
Create Date: 2022-10-06 20:37:43.098129

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86b8f7ce4c85'
down_revision = 'f2363b28258c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('video', sa.Column('title', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('video', 'title')
    # ### end Alembic commands ###
