# -*- coding: utf-8  -*-
"""
Repository to initiate and operate shares as well as retrieving share
information.
"""

from datetime import date

from sqlalchemy import Date
from sqlalchemy.sql import (
    func,
    expression
)

from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.shares import Shares
from c3smembership.data.repository.member_repository import MemberRepository
from c3smembership.data.model.base.c3smember import (
    C3sMember,
    members_shares,
)


class ShareRepository(object):
    """
    Repository class for shares.
    """

    @classmethod
    def create(cls, membership_number, shares_quantity,
               board_confirmation=None):
        """
        Create a shares package.

        Args:
            membership_number: The membership number of the member for which
                the shares package is created.
            shares_quantity: The number of shares of the package to be created.
            board_confirmation: Optional. The date on which the board of
                directors confirmed the acquisition of the shares package.

        Returns:
            The technical primary key of the created shares package.
        """
        shares = Shares(
            number=shares_quantity,
            date_of_acquisition=board_confirmation,
        )
        # pylint: disable=no-member
        member = DBSession.query(C3sMember).filter(
            C3sMember.membership_number == membership_number).first()
        # pylint: disable=no-member
        DBSession.add(shares)
        member.shares.append(shares)
        member.num_shares += shares_quantity
        DBSession.flush()
        return shares.id

    @classmethod
    def get_member_shares(cls, membership_number):
        """
        Gets the share of a members.

        Args:
            membership_number: The membership number of the member of which the
                shares are returned.

        Returns:
            The shares of the member.
        """
        # pylint: disable=no-member
        return DBSession.query(Shares) \
            .join(members_shares) \
            .join(C3sMember) \
            .filter(C3sMember.membership_number == membership_number) \
            .all()

    @classmethod
    def get_approved(cls, start_date, end_date):
        """
        Gets all shares approved between and including both start date and end
        date.

        Args:
            start_date: The first date for which approved shares are returned.
            end_date: The last date for which approved shares are returned.

        Returns:
            All shares approved between and including both start date and end
            date.
        """
        # pylint: disable=no-member
        return DBSession.query(Shares).filter(
            expression.and_(
                Shares.date_of_acquisition >= start_date,
                Shares.date_of_acquisition <= end_date)).all()

    @classmethod
    def get_approved_count(cls, start_date, end_date):
        """
        Gets the number of all shares approved between and including both start
        date and end date.

        Args:
            start_date: The first date for which approved shares are counted.
            end_date: The last date for which approved shares are counted.

        Returns:
            The number of all shares approved between and including both start
            date and end date.
        """
        # pylint: disable=no-member
        count = DBSession.query(func.sum(Shares.number)).filter(
            expression.and_(
                Shares.date_of_acquisition >= start_date,
                Shares.date_of_acquisition <= end_date)).scalar()
        if count is None:
            count = 0
        return count

    @classmethod
    def get_paid_not_approved(cls, start_date, end_date):
        """
        Gets all shares which are paid between and including both start date
        and end date but not paid until after the end date.

        Args:
            start_date: The first date for which shares are returned.
            end_date: The last date for which share are returned.

        Returns:
            All shares which are paid between and including both start date and
            end date but not paid until after the end date.

            Attributes:
                id: The technical primary key of the member
                lastname: The last name of the member
                firstname: The first name of the member
                shares_count: The number of shares
                payment_received_date: The payment date for the shares
        """
        return cls._get_paid_not_approved_query(
            'data',
            start_date,
            end_date
        ).all()

    @classmethod
    def get_paid_not_approved_count(cls, start_date, end_date):
        """
        Gets the number of all shares paid between and including both start
        date and end date but not paid after end date.

        Args:
            start_date: The first date for which shares are counted.
            end_date: The last date for which share are counted.

        Returns:
            The number of all shares paid between and including both start date
            and end date but not paid after end date.
        """
        query = cls._get_paid_not_approved_query(
            'shares_count',
            start_date,
            end_date)
        count = query.scalar()
        if count is None:
            count = 0
        return count

    @classmethod
    def _get_paid_not_approved_query(cls, query_type, start_date, end_date):
        """
        Gets the query for paid but not approved shares between and including
        start and end date.

        Args:
            query_type: The type of the query to be build. 'data' for
                retrieving rows and 'shares_count' for an aggregate count
                query.
            start_date: The first date of which paid and not approved shares
                are considered.
            end_date: The last date of which paid and not approved shares are
                considered.

        Returns:
            A query according to the specified query_type.

            For 'data' the query is build to retrieve rows with attributes 'id'
            for member id, 'lastname' for the member's lastname, 'firstname'
            for the member's firstname, 'shares_count' for the number of shares
            and 'payment_received_date' for the date on which the payment was
            received

            For 'shares_count' an aggregate count query is returned to retrieve
            the number of shares of all relevant shares packages.
        """
        # Shares which of the day of the request have not been approved are not
        # yet stored in Shares but only available on the C3sMember.

        shares_count = expression.case(
            # "== None" for SqlAlchemy instead of Python "is None"
            # pylint: disable=singleton-comparison
            [(Shares.id == None, C3sMember.num_shares)],
            else_=Shares.number
        )
        payment_received_date = expression.case(
            [(
                # "== None" for SqlAlchemy instead of Python "is None"
                # pylint: disable=singleton-comparison
                Shares.id == None,
                # C3sMember.payment_received_date has the data type DateTime
                # but Date is required as it is used in
                # Shares.payment_received_date. As CAST on DateTime '2017-01-02
                # 12:23:34.456789' returns '2017' in SQLite and therefore
                # cannot be used substring is used instead and then SQLAlchemy
                # is forced by type_coerce to parse it as a Date column.
                expression.type_coerce(
                    func.substr(C3sMember.payment_received_date, 1, 10), Date)
            )],
            else_=Shares.payment_received_date
        )
        # SqlAlchemy equality to None must be used as "== None" instead of
        # Python "is not None".
        date_of_acquisition = expression.case(
            # "== None" for SqlAlchemy instead of Python "is None"
            # pylint: disable=singleton-comparison
            [(Shares.id == None, C3sMember.membership_date)],
            else_=Shares.date_of_acquisition
        )

        if query_type == 'data':
            # pylint: disable=no-member
            query = DBSession.query(
                C3sMember.id,
                C3sMember.lastname,
                C3sMember.firstname,
                shares_count.label('shares_count'),
                payment_received_date.label('payment_received_date'),
            )
        if query_type == 'shares_count':
            # pylint: disable=no-member
            query = DBSession.query(
                func.sum(shares_count)
            )
        # Use outer joins as Shares do not have to exist yet.
        return query.select_from(C3sMember) \
            .outerjoin(members_shares) \
            .outerjoin(Shares) \
            .filter(
                expression.and_(
                    # membership not approved in time period
                    expression.or_(
                        # membership or share approved later than end date
                        date_of_acquisition > end_date,
                        # or membership or share not approved yet (default
                        # date)
                        date_of_acquisition == date(1970, 1, 1),
                    ),
                    # payment received in time period
                    payment_received_date >= start_date,
                    payment_received_date <= end_date,
                )
            )

    @classmethod
    def set_signature_reception(cls, shares_id, reception_date=None):
        """
        Sets the signature reception date.

        Args:
            shares_id: The technical primary key of the shares package for which
                the signature reception date is set.
            reception_date: Optional. The signature reception date to be set to
                the share process. If not specified the signature reception date
                is unset.
        """
        # pylint: disable=no-member
        shares = DBSession.query(Shares).filter(Shares.id == shares_id).first()
        shares.signature_received_date = reception_date
        shares.signature_received = (
            reception_date is not None
            and
            reception_date > date(1970, 1, 1)
        )

    @classmethod
    def set_signature_confirmation(cls, shares_id, confirmation_date=None):
        """
        Sets the signature reception date.

        Args:
            shares_id: The technical ID of the shares package for which the
                signature reception date is set.
            confirmation_date: Optional. The signature confirmation date to be
                set to the share process. If not specified the signature
                confirmation date is unset.
        """
        # pylint: disable=no-member
        shares = DBSession.query(Shares).filter(Shares.id == shares_id).first()
        shares.signature_confirmed_date = confirmation_date
        shares.signature_confirmed = (
            confirmation_date is not None
            and
            confirmation_date > date(1970, 1, 1)
        )

    @classmethod
    def set_payment_reception(cls, shares_id, reception_date=None):
        """
        Sets the payment confirmation of the shares package.

        Args:
            shares_id: The technical ID of the shares package for which the
                payment confirmation is set.
            reception_date: Optional. The payment reception date which is set.
                If not specified the payment reception date is unset.

        """
        # pylint: disable=no-member
        shares = DBSession.query(Shares).filter(Shares.id == shares_id).first()
        shares.payment_received_date = reception_date
        shares.payment_received = \
            reception_date is not None \
            and \
            reception_date > date(1970, 1, 1)

    @classmethod
    def set_payment_confirmation(cls, shares_id, confirmation_date=None):
        """
        Sets the payment confirmation of the shares package.

        Args:
            shares_id: The technical ID of the shares package for which the
                payment confirmation is set.
            confirmation_date: Optional. The payment confirmation date which is
                set. If not specified the payment confirmation date is unset.

        """
        # pylint: disable=no-member
        shares = DBSession.query(Shares).filter(Shares.id == shares_id).first()
        shares.payment_confirmed_date = confirmation_date
        shares.payment_confirmed = \
            confirmation_date is not None \
            and \
            confirmation_date > date(1970, 1, 1)

    @classmethod
    def set_reference_code(cls, shares_id, reference_code):
        """
        Sets the reference code of the shares package.

        Args:
            shares_id: The technical primary key of the shares package for
                which the payment confirmation is set.
            reference_code: The reference code which is set.
        """
        # pylint: disable=no-member
        shares = DBSession.query(Shares).filter(Shares.id == shares_id).first()
        shares.reference_code = reference_code

    @classmethod
    def get_share_count(cls, effective_date=None):
        """
        Gets the number of shares valid on effective date.

        Args:
            effective_date: Optional. The date for which the number of shares
                is counted. If not specified the date is set to the system
                date.
        """
        # TODO: use single optimized query
        share_count = 0
        if effective_date is None:
            effective_date = date.today()

        member_repository = MemberRepository()
        members = member_repository.get_accepted_members(effective_date)

        for member in members:
            for share in member.shares:
                if share.date_of_acquisition <= effective_date:
                    share_count += share.number
        return share_count

    @classmethod
    def get_member_share_count(cls, membership_number, effective_date=None):
        """
        Gets the number of shares of the member as of the effective_date.

        Args:
            membership_number: The business key of the member, i.e. the
                member's official membership number.
            effective_date: Optional. The effective date for which the number
                of shares is calculated.

        Returns:
            The number of shares of the member as of the effective_date.
        """
        if effective_date is None:
            effective_date = date.today()
        # pylint: disable=no-member
        share_count = DBSession \
            .query(func.sum(Shares.number)) \
            .join(members_shares) \
            .join(C3sMember) \
            .filter(
                expression.and_(
                    C3sMember.membership_number == membership_number,
                    Shares.date_of_acquisition <= effective_date
                )
            ).scalar()
        if share_count is None:
            share_count = 0
        return share_count

    @classmethod
    def get(cls, shares_id):
        """
        Gets the shares package for the specified shares id.

        Args:
            shares_id: The technical primary key of the shares package for
                which the payment confirmation is set.

        Returns:
            The shares package for the specified shares id.
        """
        # pylint: disable=no-member
        return DBSession.query(Shares).filter(Shares.id == shares_id).first()

    @classmethod
    def delete(cls, shares_id):
        """
        Deletes the shares package of the specified shares id.

        Args:
            shares_id: The technical primary key of the shares package to be
                deleted.
        """
        # pylint: disable=no-member
        DBSession.query(Shares).filter(Shares.id == shares_id).delete()
