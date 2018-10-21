# -*- coding: utf-8 -*-
"""Add extraordinary general assembly

Revision ID: 467f52a36aac
Revises: 349104ff9230
Create Date: 2018-10-21 11:28:27.440196

"""

# revision identifiers, used by Alembic.
revision = '467f52a36aac'
down_revision = '349104ff9230'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session


def upgrade():
    op.add_column('members', sa.Column('email_invite_date_bcgv18_2', sa.DateTime(), nullable=True))
    op.add_column('members', sa.Column('email_invite_flag_bcgv18_2', sa.Boolean(), nullable=True))
    op.add_column('members', sa.Column('email_invite_token_bcgv18_2', sa.Unicode(255), nullable=True))

    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(u"""
        delete from GeneralAssembly;
    """)
    session.execute(u"""
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
            (3, 3, 'Außerordentliche Generalversammlung § 13 Absatz 4 der Satzung der C3S SCE', '2015-07-16')
            ,
            (4, 4, '3. ordentliche Generalversammlung', '2016-04-17')
            ,
            (5, 5, '4. ordentliche Generalversammlung', '2017-04-02')
            ,
            (6, 6, '5. ordentliche Generalversammlung', '2018-06-03')
            ,
            (7, 7, 'Außerordentliche Generalversammlung 2018-1 nach § 13 der Satzung der C3S SCE', '2018-12-01')
        """)
    session.flush()
    session.commit()


def downgrade():
    with op.batch_alter_table('members') as batch_op:
        batch_op.drop_column('email_invite_token_bcgv18_2')
        batch_op.drop_column('email_invite_flag_bcgv18_2')
        batch_op.drop_column('email_invite_date_bcgv18_2')

    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(u"""
        delete from GeneralAssembly;
    """)
    session.execute(u"""
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
