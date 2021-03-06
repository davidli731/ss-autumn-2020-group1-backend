"""empty message

Revision ID: e3b2267d59e3
Revises: 6d4bbd6fa36b
Create Date: 2020-05-03 15:52:39.879308

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'e3b2267d59e3'
down_revision = '6d4bbd6fa36b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('circuits', 'student_id',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=False)
    op.create_unique_constraint(None, 'circuits', ['circuit_name'])
    op.drop_column('circuits', 'circuit_json')
    op.add_column('users', sa.Column('confirm_admin', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('is_admin', sa.Integer(), nullable=True))
    op.drop_index('student_id', table_name='users')
    op.drop_column('users', 'id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False))
    op.create_index('student_id', 'users', ['student_id'], unique=True)
    op.drop_column('users', 'is_admin')
    op.drop_column('users', 'confirm_admin')
    op.add_column('circuits', sa.Column('circuit_json', mysql.LONGTEXT(), nullable=False))
    op.drop_constraint(None, 'circuits', type_='unique')
    op.alter_column('circuits', 'student_id',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=True)
    # ### end Alembic commands ###
