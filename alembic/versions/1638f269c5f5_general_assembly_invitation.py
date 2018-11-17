# -*- coding: utf-8 -*-
"""General assembly invitation

Revision ID: 1638f269c5f5
Revises: 467f52a36aac
Create Date: 2018-11-11 17:06:32.115083
"""
# pylint: disable=invalid-name

from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.
revision = '1638f269c5f5'
down_revision = '467f52a36aac'


def upgrade():
    """
    Upgrade the database by creating the GeneralAssemblyInvitation table and
    migrating the data from the members table into it. Afterwards, remove the
    corresponding members attributes.
    """
    # pylint: disable=no-member
    op.create_table(
        'GeneralAssemblyInvitation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('general_assembly_id', sa.Integer(), nullable=True),
        sa.Column('member_id', sa.Integer(), nullable=True),
        sa.Column('sent', sa.DateTime(), nullable=True),
        sa.Column('token', sa.Unicode(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ['general_assembly_id'],
            ['GeneralAssembly.id'], ),
        sa.ForeignKeyConstraint(
            ['member_id'],
            ['members.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    bind = op.get_bind()
    session = Session(bind=bind)

    # 2014-08-23 1. ordentliche Generalversammlung
    session.execute("""
        insert into
            GeneralAssemblyInvitation
            (
                general_assembly_id
                ,
                member_id
                ,
                sent
                ,
                token
            )
        select
            1 as general_assembly_id
            ,
            id as member_id
            ,
            email_invite_date_bcgv14 as sent
            ,
            NULL as token
        from
            members
        where
            email_invite_flag_bcgv14 = 1
        """)

    # 2015-06-13 2. ordentliche Generalversammlung
    session.execute("""
        insert into
            GeneralAssemblyInvitation
            (
                general_assembly_id
                ,
                member_id
                ,
                sent
                ,
                token
            )
        select
            2 as general_assembly_id
            ,
            id as member_id
            ,
            email_invite_date_bcgv15 as sent
            ,
            email_invite_token_bcgv15 as token
        from
            members
        where
            email_invite_flag_bcgv15 = 1
        """)

    # 2015-07-16 Außerordentliche Generalversammlung § 13 Absatz 4 der Satzung
    # der C3S SCE
    session.execute("""
        insert into
            GeneralAssemblyInvitation
            (
                general_assembly_id
                ,
                member_id
                ,
                sent
                ,
                token
            )
        select
            3 as general_assembly_id
            ,
            id as member_id
            ,
            '2016-06-14 21:30:20.000000' as sent
            ,
            NULL as token
        from
            members
        where
            membership_accepted = 1
            and
            membership_date > '2015-06-13'
            and
            (
                membership_loss_date is NULL
                or
                membership_loss_date > '2015-06-14'
            )
        """)

    # 2016-04-17 3. ordentliche Generalversammlung
    session.execute("""
        insert into
            GeneralAssemblyInvitation
            (
                general_assembly_id
                ,
                member_id
                ,
                sent
                ,
                token
            )
        select
            4 as general_assembly_id
            ,
            id as member_id
            ,
            email_invite_date_bcgv16 as sent
            ,
            email_invite_token_bcgv16 as token
        from
            members
        where
            email_invite_flag_bcgv16 = 1
        """)

    # 2017-04-02 4. ordentliche Generalversammlung
    session.execute("""
        insert into
            GeneralAssemblyInvitation
            (
                general_assembly_id
                ,
                member_id
                ,
                sent
                ,
                token
            )
        select
            5 as general_assembly_id
            ,
            id as member_id
            ,
            email_invite_date_bcgv17 as sent
            ,
            email_invite_token_bcgv17 as token
        from
            members
        where
            email_invite_flag_bcgv17 = 1
        """)

    # 2018-06-03 5. ordentliche Generalversammlung
    session.execute("""
        insert into
            GeneralAssemblyInvitation
            (
                general_assembly_id
                ,
                member_id
                ,
                sent
                ,
                token
            )
        select
            6 as general_assembly_id
            ,
            id as member_id
            ,
            email_invite_date_bcgv18 as sent
            ,
            email_invite_token_bcgv18 as token
        from
            members
        where
            email_invite_flag_bcgv18 = 1
        """)

    # 2018-12-01 Außerordentliche Generalversammlung 2018-1 nach § 13 der
    # Satzung der C3S SCE
    session.execute("""
        insert into
            GeneralAssemblyInvitation
            (
                general_assembly_id
                ,
                member_id
                ,
                sent
                ,
                token
            )
        select
            7 as general_assembly_id
            ,
            id as member_id
            ,
            email_invite_date_bcgv18_2 as sent
            ,
            email_invite_token_bcgv18_2 as token
        from
            members
        where
            email_invite_flag_bcgv18_2 = 1
        """)

    session.execute("""
        update
            GeneralAssemblyInvitation
        set
            sent = NULL
        where
            sent = '1970-01-01 00:00:00.000000'
        """)
    session.flush()
    session.commit()
    with op.batch_alter_table('members') as batch_op:
        batch_op.drop_column('email_invite_flag_bcgv14')
        batch_op.drop_column('email_invite_date_bcgv14')
        batch_op.drop_column('email_invite_flag_bcgv15')
        batch_op.drop_column('email_invite_date_bcgv15')
        batch_op.drop_column('email_invite_token_bcgv15')
        batch_op.drop_column('email_invite_flag_bcgv16')
        batch_op.drop_column('email_invite_date_bcgv16')
        batch_op.drop_column('email_invite_token_bcgv16')
        batch_op.drop_column('email_invite_flag_bcgv17')
        batch_op.drop_column('email_invite_date_bcgv17')
        batch_op.drop_column('email_invite_token_bcgv17')
        batch_op.drop_column('email_invite_flag_bcgv18')
        batch_op.drop_column('email_invite_date_bcgv18')
        batch_op.drop_column('email_invite_token_bcgv18')


def downgrade():
    """
    Downgrade the database by recreating the members attributes, migrating back
    the data from the GeneralAssemblyInvitation table and dropping it
    afterwards.
    """
    # pylint: disable=no-member
    with op.batch_alter_table(u'members', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'email_invite_flag_bcgv14',
            sa.Boolean(),
            nullable=True,
            default=False))
        batch_op.add_column(sa.Column(
            'email_invite_date_bcgv14',
            sa.DateTime(),
            nullable=True,
            default=datetime(1970, 1, 1)))
        batch_op.add_column(sa.Column(
            'email_invite_flag_bcgv15',
            sa.Boolean(),
            nullable=True,
            default=False))
        batch_op.add_column(sa.Column(
            'email_invite_date_bcgv15',
            sa.DateTime(),
            nullable=True,
            default=datetime(1970, 1, 1)))
        batch_op.add_column(sa.Column(
            'email_invite_token_bcgv15',
            sa.Unicode(length=255),
            nullable=True))
        batch_op.add_column(sa.Column(
            'email_invite_flag_bcgv16',
            sa.Boolean(),
            nullable=True,
            default=False))
        batch_op.add_column(sa.Column(
            'email_invite_date_bcgv16',
            sa.DateTime(),
            nullable=True,
            default=datetime(1970, 1, 1)))
        batch_op.add_column(sa.Column(
            'email_invite_token_bcgv16',
            sa.Unicode(length=255),
            nullable=True))
        batch_op.add_column(sa.Column(
            'email_invite_flag_bcgv17',
            sa.Boolean(),
            nullable=True,
            default=False))
        batch_op.add_column(sa.Column(
            'email_invite_date_bcgv17',
            sa.DateTime(),
            nullable=True,
            default=datetime(1970, 1, 1)))
        batch_op.add_column(sa.Column(
            'email_invite_token_bcgv17',
            sa.Unicode(length=255),
            nullable=True))
        batch_op.add_column(sa.Column(
            'email_invite_flag_bcgv18',
            sa.Boolean(),
            nullable=True,
            default=False))
        batch_op.add_column(sa.Column(
            'email_invite_date_bcgv18',
            sa.DateTime(),
            nullable=True,
            default=datetime(1970, 1, 1)))
        batch_op.add_column(sa.Column(
            'email_invite_token_bcgv18',
            sa.Unicode(length=255),
            nullable=True))

    bind = op.get_bind()
    session = Session(bind=bind)

    # 2014-08-23 1. ordentliche Generalversammlung
    session.execute("""
        update
            members
        set
            email_invite_flag_bcgv14 = 1
            ,
            email_invite_date_bcgv14 = (
                select
                    sent
                from
                    GeneralAssemblyInvitation
                where
                    GeneralAssemblyInvitation.member_id = members.id
            )
        where
            id in (
                select
                    member_id
                from
                    GeneralAssemblyInvitation
                where
                    general_assembly_id = 1
            )
        """)

    # 2015-06-13 2. ordentliche Generalversammlung
    session.execute("""
        update
            members
        set
            email_invite_flag_bcgv15 = 1
            ,
            email_invite_date_bcgv15 = (
                select
                    sent
                from
                    GeneralAssemblyInvitation
                where
                    GeneralAssemblyInvitation.member_id = members.id
            )
            ,
            email_invite_token_bcgv15 = (
                select
                    token
                from
                    GeneralAssemblyInvitation
                where
                    GeneralAssemblyInvitation.member_id = members.id
            )
        where
            id in (
                select
                    member_id
                from
                    GeneralAssemblyInvitation
                where
                    general_assembly_id = 2
            )
        """)

    # 2016-04-17 3. ordentliche Generalversammlung
    session.execute("""
        update
            members
        set
            email_invite_flag_bcgv16 = 1
            ,
            email_invite_date_bcgv16 = (
                select
                    sent
                from
                    GeneralAssemblyInvitation
                where
                    GeneralAssemblyInvitation.member_id = members.id
            )
            ,
            email_invite_token_bcgv16 = (
                select
                    token
                from
                    GeneralAssemblyInvitation
                where
                    GeneralAssemblyInvitation.member_id = members.id
            )
        where
            id in (
                select
                    member_id
                from
                    GeneralAssemblyInvitation
                where
                    general_assembly_id = 4
            )
        """)

    # 2017-04-02 4. ordentliche Generalversammlung
    session.execute("""
        update
            members
        set
            email_invite_flag_bcgv17 = 1
            ,
            email_invite_date_bcgv17 = (
                select
                    sent
                from
                    GeneralAssemblyInvitation
                where
                    GeneralAssemblyInvitation.member_id = members.id
            )
            ,
            email_invite_token_bcgv17 = (
                select
                    token
                from
                    GeneralAssemblyInvitation
                where
                    GeneralAssemblyInvitation.member_id = members.id
            )
        where
            id in (
                select
                    member_id
                from
                    GeneralAssemblyInvitation
                where
                    general_assembly_id = 5
            )
        """)

    # 2018-06-03 5. ordentliche Generalversammlung
    session.execute("""
        update
            members
        set
            email_invite_flag_bcgv18 = 1
            ,
            email_invite_date_bcgv18 = (
                select
                    sent
                from
                    GeneralAssemblyInvitation
                where
                    GeneralAssemblyInvitation.member_id = members.id
            )
            ,
            email_invite_token_bcgv18 = (
                select
                    token
                from
                    GeneralAssemblyInvitation
                where
                    GeneralAssemblyInvitation.member_id = members.id
            )
        where
            id in (
                select
                    member_id
                from
                    GeneralAssemblyInvitation
                where
                    general_assembly_id = 6
            )
        """)

    # 2018-12-01 Außerordentliche Generalversammlung 2018-1 nach § 13 der
    # Satzung der C3S SCE
    session.execute("""
        update
            members
        set
            email_invite_flag_bcgv18_2 = 1
            ,
            email_invite_date_bcgv18_2 = (
                select
                    sent
                from
                    GeneralAssemblyInvitation
                where
                    GeneralAssemblyInvitation.member_id = members.id
            )
            ,
            email_invite_token_bcgv18_2 = (
                select
                    token
                from
                    GeneralAssemblyInvitation
                where
                    GeneralAssemblyInvitation.member_id = members.id
            )
        where
            id in (
                select
                    member_id
                from
                    GeneralAssemblyInvitation
                where
                    general_assembly_id = 7
            )
        """)

    op.drop_table('GeneralAssemblyInvitation')
