"""Add kw.comment

Revision ID: 5366c8856d5
Revises: 396ce835f1b
Create Date: 2017-03-18 13:55:05.182134

"""

# revision identifiers, used by Alembic.
revision = '5366c8856d5'
down_revision = '396ce835f1b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('keywords', sa.Column('comment', sa.String(length=512), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('keywords', 'comment')
    ### end Alembic commands ###