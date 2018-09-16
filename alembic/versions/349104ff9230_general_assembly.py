"""General assembly

Revision ID: 349104ff9230
Revises: 4a12432fa915
Create Date: 2018-09-01 21:44:05.934286

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = '349104ff9230'
down_revision = '4a12432fa915'


def upgrade():
    op.create_table(
        'GeneralAssembly',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=True),
        sa.Column('name', sa.Unicode(length=255), nullable=True),
        sa.Column('date', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute("""
        insert into
            GeneralAssembly
            (
                id
                ,
                number
                ,
                name
                ,
                date
            )
        values
            (1, 1, '1. ordentliche Generalversammlung', '2014-08-23')
            ,
            (2, 2, '2. ordentliche Generalversammlung', '2015-06-13')
            ,
            (3, 3, '3. ordentliche Generalversammlung', '2016-04-17')
            ,
            (4, 4, '4. ordentliche Generalversammlung', '2017-04-02')
            ,
            (5, 5, '5. ordentliche Generalversammlung', '2018-06-03')
        """)
    session.flush()
    session.commit()


def downgrade():
    op.drop_table('GeneralAssembly')
