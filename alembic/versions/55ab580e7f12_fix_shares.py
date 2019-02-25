"""Fix shares

Revision ID: 55ab580e7f12
Revises: 9f0baac0c2
Create Date: 2019-02-25 22:29:14.862847

"""

from alembic import op
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = '55ab580e7f12'
down_revision = '9f0baac0c2'


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute("""
        update
            shares
        set
            payment_received_date = (
                select
                    substr(members.payment_received_date, 1, 10)
                from
                    members
                join
                    members_shares
                    on
                    members_shares.members_id = members.id
                where
                    members_shares.shares_id = shares.id
            )
            ,
            -- Get payment_confirmed_date from member to which the share
            -- belongs
            payment_confirmed_date = (
                select
                    substr(members.payment_confirmed_date, 1, 10)
                from
                    members
                join
                    members_shares
                    on
                    members_shares.members_id = members.id
                where
                    members_shares.shares_id = shares.id
            )
            ,
            -- Get signature_confirmed_date from member to which the share
            -- belongs
            signature_confirmed_date = (
                select
                    substr(members.signature_confirmed_date, 1, 10)
                from
                    members
                join
                    members_shares
                    on
                    members_shares.members_id = members.id
                where
                    members_shares.shares_id = shares.id
            )
        where
            id in (
                -- Faulty rows are identified by having payment_received_date
                -- and signature_received_date but the corresponding member
                -- does have the payment_received_date set.
                select
                    s.id
                from
                    members m
                join
                    members_shares ms
                    on
                    ms.members_id = m.id
                join
                    shares s
                    on
                    s.id = ms.shares_id
                where
                    s.payment_received_date = '1970-01-01'
                    and
                    s.signature_confirmed_date = '1970-01-01'
                    and
                    substr(m.payment_received_date, 1, 10) != '1970-01-01'
            )
    """)
    session.flush()
    session.commit()


def downgrade():
    # The upgrade is a bug fix. This bug fix should not be downgraded to
    # introduce re-inconsistent data. Furthermore, the bug fix cannot be
    # downgraded because there is no way anymore to identify the then correct
    # data.
    pass
