# -*- coding: utf-8  -*-
"""
C3sMember
"""

from datetime import (
    date,
    datetime,
)
import re

from sqlalchemy import (
    and_,
    Boolean,
    Column,
    Date,
    DateTime,
    distinct,
    ForeignKey,
    Integer,
    or_,
    not_,
    Table,
    Unicode,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import (
    relationship,
    synonym
)

from c3smembership.data.model.base import (
    Base,
    check_password,
    DBSession,
    hash_password,
)
from c3smembership.data.model.base.dues import Dues
from c3smembership.data.model.base.shares import Shares


# pylint: disable=no-member


class InvalidPropertyException(Exception):
    """
    Exception indicating an invalid property value.
    """
    pass


class InvalidSortDirection(Exception):
    """
    Exception indicating an invalid sort direction.
    """
    pass


# table for relation between membership and shares
# pylint: disable=invalid-name
members_shares = Table(
    'members_shares', Base.metadata,
    Column(
        'members_id', Integer, ForeignKey('members.id'),
        primary_key=True, nullable=False),
    Column(
        'shares_id', Integer, ForeignKey('shares.id'),
        primary_key=True, nullable=False)
)


class C3sMember(Base):
    """
    This table holds datasets from submissions to the C3S AFM form
    (AFM = application for membership),
    as well as members who have completed the process
    of becoming a member.

    Apart from datasets from the original form,
    other datasets have found their way into the database
    through imports: crowdfunders and founding members, for example.

    * The crowdfunders were gathered through a CF platform.
    * The founders from the initial assembly (RL! Hamburg!)
    * legal entities (we had a form on dead wood)

    Some attributes have been added over time to cater for different needs.
    """
    __tablename__ = 'members'
    # pylint: disable=invalid-name
    id = Column(Integer, primary_key=True)
    """technical id. / number in table (integer, primary key)"""

    # personal information
    """
    **personal information**
    """
    firstname = Column(Unicode(255))
    """given name(s) of person"""
    lastname = Column(Unicode(255))
    """last name of person"""
    email = Column(Unicode(255))
    """email address of person
    """
    _password = Column('password', Unicode(60))
    """password hash of person
    """
    last_password_change = Column(
        DateTime,
        default=func.current_timestamp())
    """timestamp of password persistence (time of submission)
    """
    # pass_reset_token = Column(Unicode(255))
    address1 = Column(Unicode(255))
    """Street & Number"""
    address2 = Column(Unicode(255))
    """Address continued"""
    postcode = Column(Unicode(255))
    """Postal Code"""
    city = Column(Unicode(255))
    """City or Place"""
    country = Column(Unicode(255))
    """Country"""
    locale = Column(Unicode(255))
    """The Language chosen by a member when filling out the form.

    We remember this so we know which language to address her with.
    """
    date_of_birth = Column(Date(), nullable=False)
    email_is_confirmed = Column(Boolean, default=False)
    email_confirm_code = Column(Unicode(255), unique=True)  # reference code
    """The Code used as reference when registering for membership:

    * contained in URL of link applicants have to use to get their PDF.
    * used for bank transfer reference

    """
    email_confirm_token = Column(Unicode(255), unique=True)  # token
    '''Unicode'''
    email_confirm_mail_date = Column(
        DateTime(), default=datetime(1970, 1, 1))
    # duplicate entries // people submitting at different times
    is_duplicate = Column(Boolean, default=False)
    """boolean

    * flag for entries that are known duplicates of other applications
      if person has already applied before.
    """
    is_duplicate_of = Column(Integer, nullable=True)
    """Integer

    * id of entry considered as original or relevant for membership
    """
    # shares
    num_shares = Column(Integer())
    """Integer

    * The number of shares from the time of afm submission
    * Then application is approved, this number of shares is turned into
      an entry in the shares list below, referencing a shares package
      which is persisted in the Shares table.

    .. note:: For accepted members, this is not necessarily the total
       number of shares, as members can hold several packages,
       from different times of acquisition.

    """
    date_of_submission = Column(DateTime(), nullable=False)
    """datetime

    * the date and time this application was submitted
    """
    signature_received = Column(Boolean, default=False)
    """Boolean

    * Has the signature been received?
    """
    signature_received_date = Column(
        DateTime(), default=datetime(1970, 1, 1))
    """datetime

    * the date and time this application was submitted
    """
    signature_confirmed = Column(Boolean, default=False)
    """Boolean

    * Has reception of signed form been confirmed?
    """
    signature_confirmed_date = Column(
        DateTime(), default=datetime(1970, 1, 1))
    """datetime

    * the date and time arrival of signed form was confirmed per email
    """
    payment_received = Column(Boolean, default=False)
    """Boolean

    * Has the payment been received?
    """
    payment_received_date = Column(
        DateTime(), default=datetime(1970, 1, 1))
    """datetime

    * the date and time payment for this application was received
    """
    payment_confirmed = Column(Boolean, default=False)
    """Boolean

    * Has the payment been confirmed?
    """
    payment_confirmed_date = Column(
        DateTime(), default=datetime(1970, 1, 1))
    """datetime

    * the date and time this application was confirmed per email
    """
    # shares in other table
    shares = relationship(
        Shares,
        secondary=members_shares,
        backref="members"
    )
    """relation

    * list of shares packages a member has acquired.
    * has entries as soon as an application for membership has been approved
      by the board of directors -- and the relevant date of approval
      has been entered into the system by staff.
    """
    # reminders
    sent_signature_reminder = Column(Integer, default=0)
    """Integer

    * stores how many signature reminders have been sent out
    """
    sent_signature_reminder_date = Column(
        DateTime(), default=datetime(1970, 1, 1))
    """DateTime

    * stores *when* the last signature reminder was sent out
    """
    sent_payment_reminder = Column(Integer, default=0)
    """Integer

    * stores how many payment reminders have been sent out
    """
    sent_payment_reminder_date = Column(
        DateTime(), default=datetime(1970, 1, 1))
    """DateTime

    * stores *when* the last payment reminder was sent out
    """
    # comment
    accountant_comment = Column(Unicode(255))
    # membership information
    membership_type = Column(Unicode(255))
    """Unicode

    * Type of membership. either one of

       * normal (persons, artists)
       * investing (non-artist persons or legal entities)
    """
    member_of_colsoc = Column(Boolean, default=False)
    """Boolean

    * is member of other collecting society
    """
    name_of_colsoc = Column(Unicode(255))
    """Unicode

    * name(s) of other collecting societies
    """
    # acquisition of membership
    membership_accepted = Column(Boolean, default=False)
    """Boolean

    * has the membersip been accepted by the board of directors?
    """
    membership_date = Column(Date(), default=date(1970, 1, 1))
    """Date

    Date of membership approval by the board.
    """
    membership_number = Column(Integer())
    """Integer

    * Membership Number given upon approval.
    """
    # ## loss of membership
    # the date on which the membership terminates, i.e. the date of
    # membership and the day after which the membership does no longer exist
    membership_loss_date = Column(Date())
    # the membership can be lost upon:
    # - resignation
    # - expulsion
    # - death
    # - bankruptcy
    # - transfer of remaining shares
    membership_loss_type = Column(Unicode(255))

    # startnex repair operations
    mtype_confirm_token = Column(Unicode(255))
    mtype_email_date = Column(DateTime(), default=datetime(1970, 1, 1))

    # legal entities
    is_legalentity = Column(Boolean, default=False)
    court_of_law = Column(Unicode(255))
    registration_number = Column(Unicode(255))
    # membership certificate
    certificate_email = Column(Boolean, default=False)
    certificate_token = Column(Unicode(10))
    certificate_email_date = Column(DateTime())

    # membership dues per year are stored in the Dues table, one row per member
    # and year. See c3smembership.data.model.base.dues.Dues.
    dues = relationship(
        Dues,
        backref='member',
        order_by='Dues.year',
        cascade='all, delete-orphan',
    )
    """relation

    * list of dues accounts of the member, one per year.
    """

    # privacy
    privacy_consent = Column(DateTime(), nullable=True)

    def __init__(self, firstname, lastname, email, password,
                 address1, address2, postcode, city, country, locale,
                 date_of_birth, email_is_confirmed, email_confirm_code,
                 num_shares,
                 date_of_submission,
                 membership_type, member_of_colsoc, name_of_colsoc,
                 privacy_consent=None):
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.password = password
        self.last_password_change = datetime.now()
        self.address1 = address1
        self.address2 = address2
        self.postcode = postcode
        self.city = city
        self.country = country
        self.locale = locale
        self.date_of_birth = date_of_birth
        self.email_is_confirmed = email_is_confirmed
        self.email_confirm_code = email_confirm_code
        self.num_shares = num_shares
        self.date_of_submission = date_of_submission
        self.signature_received = False
        self.payment_received = False
        self.membership_type = membership_type
        self.member_of_colsoc = member_of_colsoc
        self.privacy_consent = privacy_consent
        if self.member_of_colsoc is True:
            self.name_of_colsoc = name_of_colsoc
        else:
            self.name_of_colsoc = ''

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = hash_password(password)

    password = property(_get_password, _set_password)
    password = synonym('_password', descriptor=password)

    def get_dues(self, year, create=True):
        """
        Get the member's dues account for the year.

        If no dues account exists for the year yet and ``create`` is True a new
        one is created, attached to the member (and thereby persisted) and
        returned. If ``create`` is False a transient, non-persisted account with
        default values is returned instead, which is useful for read-only access
        like display.

        Args:
            year (int): The dues year, e.g. 2026.
            create (bool): Whether a missing account is attached to the member
                and thereby persisted. Defaults to True.

        Returns:
            The Dues account of the member for the year.
        """
        for dues in self.dues:
            if dues.year == year:
                return dues
        dues = Dues(member_id=self.id, year=year)
        if create:
            self.dues.append(dues)
        return dues

    @classmethod
    def get_by_code(cls, email_confirm_code):
        """
        Find a member by confirmation code

        This is needed when a user returns from reading her email
        and clicking on a link containing the confirmation code.
        As the code is unique, one record is returned.

        Returns:
           object: C3sMember object
        """
        return DBSession.query(cls).filter(
            cls.email_confirm_code == email_confirm_code).first()

    @classmethod
    def check_for_existing_confirm_code(cls, email_confirm_code):
        """
        check if a code is already present
        """
        check = DBSession.query(cls).filter(
            cls.email_confirm_code == email_confirm_code).first()
        return check is not None

    @classmethod
    def get_by_id(cls, member_id):
        """
        Get one C3sMember object by id.

        Returns:
            * **C3sMember object**, if id exists.
            * **None**, if id does not exist.
        """
        return DBSession.query(cls).filter(cls.id == member_id).first()

    @classmethod
    def get_by_email(cls, email):
        """return one or more members by email (a list!)"""
        return DBSession.query(cls).filter(cls.email == email).all()

    @classmethod
    def get_all(cls):
        """return all afms and members"""
        return DBSession.query(cls).all()

    @classmethod
    def get_dues_invoicees(cls, year, num):
        """
        Get a given number *n* of members to send dues invoices to.

        Queries the database for members, where

        * members are accepted
        * members have not received their dues invoice email yet for the year
        * membership started within or before the dues year
        * membership is normal or investing
        * membership had not been lost before the dues year

        Args:
          year is the dues year, e.g. 2026
          num is the number *n* of C3sMembers to return

        Returns:
          a list of *n* member objects
        """
        # In SqlAlchemy the True comparison must be done as "a == True" and not
        # in the python default way "a is True". Therefore:
        # pylint: disable=singleton-comparison
        return DBSession.query(cls).filter(
            and_(
                cls.membership_accepted == True,
                ~cls.dues.any(
                    and_(Dues.year == year, Dues.invoice == True)),
                cls.membership_date < date(year + 1, 1, 1),
                cls.membership_type.in_(['normal', 'investing']),
                or_(
                    cls.membership_loss_date == None,
                    cls.membership_loss_date >= date(year, 1, 1),
                ),
            )).slice(0, num).all()

    @classmethod
    def delete_by_id(cls, member_id):
        """
        Delete one C3sMember entry by id.

        Args:
            _id: the id to delete

        Returns:
            * **1** on success
            * **0** else
        """
        return DBSession.query(cls).filter(cls.id == member_id).delete()

    # listings
    @classmethod
    def get_duplicates(cls):
        """
        Get all duplicates: C3sMember entries tagged as duplicates.

        Used in:
            membership_list, statistics_view

        Returns:
            list: list of C3sMember entries flagged as duplicates.
        """
        return DBSession.query(cls).filter(
            cls.is_duplicate == 1).all()

    @classmethod
    def get_members(cls, order_by, how_many=10, offset=0, order="asc"):
        """
        Compute a list of C3sMember items with membership accepted (Query!).

        Args:
            order_by: which column to sort on, e.g. "id"
            how_many: number of entries (Integer)
            offset: how many to omit (leave out first n; default is 0)
            order: either "asc" (ascending, **default**) or "desc" (descending)

        Raises:
            Exception: invalid value for "order_by" or "order".

        Returns:
            query: C3sMember database query
        """
        try:
            attr = getattr(cls, order_by)
            order_function = getattr(attr, order)
        except:
            raise Exception("Invalid order_by ({0}) or order value "
                            "({1})".format(order_by, order))
        count = int(offset) + int(how_many)
        offset = int(offset)
        query = DBSession.query(cls).filter(
            cls.membership_accepted == 1
        ).order_by(order_function()).slice(offset, count)
        return query

    # statistical stuff
    @classmethod
    def get_postal_codes_de(cls):
        """
        Get postal codes of C3sMember entries from germany

        Returns:
            bag (list containing duplicates): postal codes in DE"""
        rows = DBSession.query(cls).filter(
            cls.country == 'DE'
        ).all()
        postal_codes_de = []
        for row in rows:
            try:
                int(row.postcode)
                if len(row.postcode) == 5:
                    postal_codes_de.append(row.postcode)
            except ValueError:
                pass
        return postal_codes_de

    # statistical stuff

    @classmethod
    def get_number(cls):
        """
        Count number of entries in C3sMember table (by counting rows)

        Used in:
            statistics_view, membership_list, import_export, some tests...

        Returns:
            Integer: number
        """
        return DBSession.query(cls).count()

    @classmethod
    def get_num_members_accepted(cls):
        """
        Count the entries that have actually been accepted as members.

        Used in:
            statistics_view, membership_list

        Returns:
            Integer: number
        """
        return DBSession.query(
            cls).filter(cls.is_member_filter()).count()

    @classmethod
    def get_num_non_accepted(cls):
        """
        Count the applications that have **not** been accepted as members.

        TODO: how about duplicates!?

        Returns:
            Integer: number of C3sMember entries.
        """
        return DBSession.query(cls).filter(
            not_(cls.membership_accepted_filter())).count()

    @classmethod
    def get_num_mem_nat_acc(cls):
        """
        Count the *persons* that have actually been accepted as members.

        Used in:
            statistics_view

        Returns:
            Integer: number
        """
        return DBSession.query(cls).filter(
            cls.is_legalentity == 0,
            cls.is_member_filter(),
        ).count()

    @classmethod
    def get_num_mem_jur_acc(cls):
        """
        Count the *legal entities* that have actually been accepted as members.

        Used in:
            statistics_view

        Returns:
            Integer: number
        """
        return DBSession.query(cls).filter(
            cls.is_legalentity == 1,
            cls.is_member_filter(),
        ).count()

    @classmethod
    def get_num_mem_norm(cls):
        """
        Count the memberships that are normal members.

        Used in:
            statistics_view

        Returns:
            Integer: number
        """
        return DBSession.query(cls).filter(
            cls.is_member_filter(),
            cls.membership_type == 'normal'
        ).count()

    @classmethod
    def get_num_mem_invest(cls):
        """
        Count the memberships that are investing members.

        Used in:
            statistics_view

        Returns:
            Integer: number
        """
        return DBSession.query(cls).filter(
            cls.is_member_filter(),
            cls.membership_type == 'investing'
        ).count()

    @classmethod
    def get_num_mem_other_features(cls):
        """
        Count the memberships that are neither normal nor investing members.

        Used in:
            statistics_view

        Returns:
            Integer: number
        """
        return DBSession.query(cls).filter(
            cls.is_member_filter(),
            cls.membership_type != 'normal',
            cls.membership_type != 'investing'
        ).count()

    @classmethod
    def get_num_membership_lost(cls):
        """
        Gets the number of members which lost membership before today.

        Returns:
            Integer: number
        """
        return DBSession.query(cls).filter(cls.membership_lost_filter()).count()

    # listings
    @classmethod
    def member_listing(cls, order_by, how_many=10, offset=0, order="asc"):
        """
        Compute a list of C3sMember items (Query!).

        Note:
            these are not necessarily accepted members!

        Used in:
            membership_list, import_export

        Args:
            order_by: which column to sort on, e.g. "id"
            how_many: number of entries (Integer)
            offset: how many to omit (leave out first n; default is 0)
            order: either "asc" (ascending, **default**) or "desc" (descending)

        Raises:
            Exception: invalid value for "order_by" or "order".

        Returns:
            query: C3sMember database query
        """
        try:
            attr = getattr(cls, order_by)
            order_function = getattr(attr, order)
        except:
            raise Exception("Invalid order_by ({0}) or order value "
                            "({1})".format(order_by, order))
        count = int(offset) + int(how_many)
        offset = int(offset)
        query = DBSession.query(cls).order_by(order_function())\
            .slice(offset, count)
        return query

    @classmethod
    def get_range_ids(cls, order_by, first_id, last_id, order="asc"):
        """
        Get a list of C3sMember items by range of ids.

        Used in:
            membership_list

        Args:
            order_by: which column to sort on, e.g. "id"
            first_id: id of first entry (Integer)
            last_id: id of last entry (Integer)
            order: either "asc" (ascending, **default**) or "desc" (descending)

        Raises:
            Exception: invalid value for "order_by" or "order".

        Returns:
            list: C3sMembership objects
        """
        try:
            attr = getattr(cls, order_by)
            order_function = getattr(attr, order)
        except:
            raise Exception("Invalid order_by ({0}) or order value "
                            "({1})".format(order_by, order))
        query = DBSession.query(cls).filter(
            and_(
                cls.id >= first_id,
                cls.id <= last_id,
            )
        ).order_by(order_function()).all()
        return query

    @classmethod
    def nonmember_listing(cls, offset, page_size, sort_property,
                          sort_direction='asc'):
        """
        Retrieve a list of members which are **not** accepted.
        Note:
            These are membership applicants which have not been accepted, yet.

        Used in:
            accountants_views

        Args:
            offset: How many to omit (leave out first n; default is 0)
            page_size: Number of entries per page (Integer)
            sort_property: Which column to sort on, e.g. "id"
            sort_direction: Either "asc" (ascending, **default**) or "desc"
                (descending)

        Raises:
            InvalidPropertyException: The sort property does not exist.
            InvalidSortDirection: The sort direction is invalid.

        Returns:
            List of C3sMember objects.
        """
        try:
            sort_attribute = getattr(cls, sort_property)
        except AttributeError:
            raise InvalidPropertyException(
                'C3sMember does not have a property named "{0}".'.format(
                    sort_property))
        try:
            order_function = getattr(sort_attribute, sort_direction)
        except AttributeError:
            raise InvalidSortDirection(
                'Invalid sort direction: {0}'.format(sort_direction))
        query = DBSession.query(cls).filter(
            or_(
                cls.membership_accepted == 0,
                cls.membership_accepted == '',
                # pylint: disable=singleton-comparison
                # noqa
                cls.membership_accepted == None,
            )
        ).order_by(
            order_function()
        ).slice(offset, offset + page_size)
        return query.all()

    @classmethod
    def nonmember_listing_count(cls):
        """
        Gets the number of applicants which have not been accepted as members
        yet.
        """
        query = DBSession.query(cls).filter(
            or_(
                cls.membership_accepted == 0,
                cls.membership_accepted == '',
                # pylint: disable=singleton-comparison
                # noqa
                cls.membership_accepted == None,
            )
        ).count()
        return query

    # count for statistics
    @classmethod
    def afm_num_shares_unpaid(cls):
        """
        Gets the number of shares for which membership applicant has not yet
        paid the price.
        """
        rows = DBSession.query(cls).all()
        num_shares_unpaid = 0
        for row in rows:
            if not row.payment_received:
                num_shares_unpaid += row.num_shares
        return num_shares_unpaid

    @classmethod
    def afm_num_shares_paid(cls):
        """
        Gets the number of shares for which membership applicant has already
        paid the price.
        """
        rows = DBSession.query(cls).all()
        num_shares_paid = 0
        for row in rows:
            if row.payment_received:
                num_shares_paid += row.num_shares
        return num_shares_paid

    # workflow: need approval by the board
    @classmethod
    def afms_ready_for_approval(cls):
        """
        Gets the list of membership applicants who can be granted membership by
        the board of directors because they have fulfilled their duty of
        sending in a signed membership application as well as paying the
        share's price.
        """
        return DBSession.query(cls).filter(
            and_(
                (cls.membership_accepted == 0),
                (cls.signature_received),
                (cls.payment_received),
            )).all()

    # autocomplete
    @classmethod
    def get_matching_codes(cls, prefix):
        """
        Return only codes matching the prefix.

        This is used in the autocomplete form to search for C3sMember entries.

        Returns:
            list of strings
        """
        rows = DBSession.query(cls).all()
        codes = []
        for row in rows:
            if row.email_confirm_code.startswith(prefix):
                codes.append(row.email_confirm_code)
        return codes

    @classmethod
    def check_password(cls, member_id, password):
        """
        Check a password against the database.

        Args:
            member_id: C3sMember entry id.
            password: a password supplied

        Returns:
            the answer of bcrypt.crypt, comparing the password supplied
                and the hash from the database
        """
        member = cls.get_by_id(member_id)
        return check_password(member.password, password)

    # this one is used by RequestWithUserAttribute
    @classmethod
    def check_user_or_none(cls, member_id):
        """
        Check whether a user by that username exists in the database.

        Used in:
            security.request.RequestWithUserAttribute

        Args:
            member_id: id of C3sMember entry.
        Returns:
            object, if id exists, else None.
            None: if id
        """
        login = cls.get_by_id(member_id)  # is None if user not exists
        return login

    # for merge comparisons
    @classmethod
    def get_same_lastnames(cls, lastname):
        """return list of accepted members with same lastnames"""
        return DBSession.query(cls).filter(
            and_(
                cls.membership_accepted == 1,
                cls.lastname == lastname
            )).all()

    @classmethod
    def get_same_firstnames(cls, firstname):
        """return list of accepted members with same fistnames"""
        return DBSession.query(cls).filter(
            and_(
                cls.membership_accepted == 1,
                cls.firstname == firstname
            )).all()

    @classmethod
    def get_same_email(cls, email):
        """return list of accepted members with same email"""
        return DBSession.query(cls).filter(
            and_(
                cls.membership_accepted == 1,
                cls.email == email,
            )).all()

    @classmethod
    def get_same_date_of_birth(cls, date_of_birth):
        """return list of accepted members with same date of birth"""
        return DBSession.query(cls).filter(
            and_(
                cls.membership_accepted == 1,
                cls.date_of_birth == date_of_birth,
            )).all()

    # membership numbers etc.
    @classmethod
    def get_num_membership_numbers(cls):
        """
        count the number of membership numbers
        """
        return DBSession.query(cls).filter(cls.membership_number).count()

    @classmethod
    def get_next_free_membership_number(cls):
        """
        returns the next free membership number
        """
        return C3sMember.get_highest_membership_number() + 1

    @classmethod
    def get_highest_membership_number(cls):
        """
        get the highest membership number
        """
        rows = DBSession.query(cls.membership_number).filter(
            cls.membership_number != None).all()  # noqa
        membership_numbers = []
        for row in rows:
            membership_numbers.append(int(row[0]))
        try:
            max_number = max(membership_numbers)
        except ValueError:
            membership_numbers = [0, 999999999]
            max_number = 999999999
        try:
            assert(max_number == 999999999)
            membership_numbers.remove(max(membership_numbers))  # remove known maximum
        except AssertionError:
            pass
        return max(membership_numbers)

    # countries
    @classmethod
    def get_num_countries(cls):
        """return number of countries in DB"""
        return DBSession.query(func.count(distinct(cls.country))).scalar()

    @classmethod
    def get_countries_list(cls):
        """return dict of countries and number of occurrences"""
        countries = {}
        rows = DBSession.query(cls)
        for row in rows:
            if row.country not in list(countries.keys()):
                countries[row.country] = 1
            else:
                countries[row.country] += 1
        return countries

    # autocomplete
    @classmethod
    def get_matching_people(cls, prefix):
        """
        return only entries matchint the prefix
        """
        rows = DBSession.query(cls).all()
        names = {}
        for row in rows:
            if row.lastname.startswith(prefix):
                key = (
                    row.email_confirm_code + ' ' +
                    row.lastname + ', ' + row.firstname)
                names[key] = key
        return names


    def get_url_safe_name(self):
        """
        Gets a url-safe version of the member's name in which all characters
        except 0-9, a-z and A-Z are replaced by a dash.
        """
        return re.sub(  # # replace characters
            '[^0-9a-zA-Z]',  # other than these
            '-',  # with a -
            self.lastname if self.is_legalentity else (
                self.lastname + self.firstname))

    def is_member(self, effective_date=None):
        """
        Indicates whether the entity is still a member.

        For being a member the membership must have been accepted and the
        membership must not have been lost.
        """
        if effective_date is None:
            effective_date = date.today()
        membership_lost = (
            self.membership_loss_date is not None
            and
            self.membership_loss_date < effective_date)
        membership_accepted = (
            self.membership_accepted
            and
            self.membership_date is not None
            and
            self.membership_date <= effective_date)
        return membership_accepted and not membership_lost

    @classmethod
    def membership_lost_filter(cls, effective_date=None):
        """
        Provides a SqlAlchemy filter only matching entities which lost
        membership before the specified effective date.

        Args:
            effective_date: Optional. The date before which the membership was
                lost. If not specified then the current date of is used.

        Returns:
            A filter only matching entities which lost membership before the
            specified effective date.
        """
        if effective_date is None:
            effective_date = date.today()
        return and_(
            cls.membership_loss_date != None,
            cls.membership_loss_date < effective_date)

    @classmethod
    def membership_accepted_filter(cls, effective_date=None):
        """
        Provides a SqlAlchemy filter only matching entities which had their
        membership accepted before or on the specified effective date.

        Args:
            effective_date: Optional. The date before or on which the membership
                was accepted. If not specified then the current date of is used.

        Returns:
            A filter only matching entities which had their membership accepted
            before or on the specified effective date.
        """
        if effective_date is None:
            effective_date = date.today()
        return and_(
            cls.membership_accepted,
            cls.membership_date != None,
            cls.membership_date <= effective_date)

    @classmethod
    def is_member_filter(cls, effective_date=None):
        """
        Provides a SqlAlchemy filter only matching entities which are members at
        the specified effective date.

        For being a member the membership must have been accepted and the
        membership must not have been lost.

        Args:
            effective_date: Optional. The date for which the membership status
                is checked. If not specified then the current date of is used.

        Returns:
            A filter matching all entities which are members as the specified
            effective date.
        """
        if effective_date is None:
            effective_date = date.today()
        return and_(
            cls.membership_accepted_filter(effective_date),
            not_(cls.membership_lost_filter(effective_date)))
