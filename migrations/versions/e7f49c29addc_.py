"""empty message

Revision ID: e7f49c29addc
Revises: 5a1e7bcc4be4
Create Date: 2021-08-19 22:31:12.863442

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7f49c29addc'
down_revision = '5a1e7bcc4be4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('community_member', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('community_member', 'community_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('community_member', 'id')
    op.alter_column('community_post', 'post_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('community_post', 'community_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('community_post', 'id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('community_post', sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.alter_column('community_post', 'community_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('community_post', 'post_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.add_column('community_member', sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.alter_column('community_member', 'community_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('community_member', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###
