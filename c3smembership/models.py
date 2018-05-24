# -*- coding: utf-8  -*-
"""
This module holds the database models for c3sMembership.

Unit and functional tests for the code are in tests/test_models.py.
Other functional and integration tests can be found throughout the
other bits of tests and code relying on or using these models.

The classes below represent the database tables.
It is actually a SQLAlchemy model.

Classes / Data Objects:

* **Groups** (Roles for Users)
* **C3sStaff** (backend login people, administration)
* **Shares** (packages -- members can hold packages of shares)
* **C3sMember** (members .. or applications to become members)
* **Dues15Invoice** (membership dues, 2015 edition)
"""

from datetime import (
    date,
    datetime,
)
from decimal import Decimal
import math
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
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from sqlalchemy.sql import expression
from sqlalchemy.orm import (
    relationship,
    synonym
)
import sqlalchemy.types as types
import cryptacular.bcrypt

from c3smembership.data.model.base import (
    Base,
    DBSession,
)


# pylint: disable=no-member


CRYPT = cryptacular.bcrypt.BCRYPTPasswordManager()


def hash_password(password):
    """
    Calculates the password hash.
    """
    return unicode(CRYPT.encode(password))


# TODO: Use standard SQLAlchemy Decimal when a database is used which supports
# it.
class SqliteDecimal(types.TypeDecorator):
    """
    Type decorator for persisting Decimal (currency values)

    TODO: Use standard SQLAlchemy Decimal
    when a database is used which supports it.
    """
    impl = types.String

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(100))

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        else:
            return None

    def process_result_value(self, value, dialect):
        if value is not None and value != '':
            return Decimal(value)
        else:
            return None

DatabaseDecimal = SqliteDecimal


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


class Group(Base):
    """
    The table of Groups.

    aka roles for users.

    Users in group 'staff' may do things others may not.
    """
    __tablename__ = 'groups'
    # pylint: disable=invalid-name
    id = Column(Integer, primary_key=True, nullable=False)
    """technical id. / number in table (Integer, Primary Key)"""
    name = Column(Unicode(30), unique=True, nullable=False)
    """name of the group (Unicode)"""
    def __str__(self):
        return 'group:%s' % self.name

    def __init__(self, name):
        self.name = name

    @classmethod
    def get_staffers_group(cls, groupname=u'staff'):
        """
        Get the "staff" group.

        Returns:
            object: staff group.
        """
        dbsession = DBSession()
        staff_group = dbsession.query(
            cls).filter(cls.name == groupname).first()
        return staff_group


# table for relation between staffers and groups
# pylint: disable=invalid-name
staff_groups = Table(
    'staff_groups', Base.metadata,
    Column(
        'staff_id', Integer, ForeignKey('staff.id'),
        primary_key=True, nullable=False),
    Column(
        'group_id', Integer, ForeignKey('groups.id'),
        primary_key=True, nullable=False)
)
# """
# Table for relation of staff to groups
# """


class C3sStaff(Base):
    """
    C3S staff may login and do things.

    """
    __tablename__ = 'staff'
    # pylint: disable=invalid-name
    id = Column(Integer, primary_key=True)
    """technical id. / number in table (integer, primary key)"""
    login = Column(Unicode(255), unique=True)
    """every user has a login name. (unicode)"""
    _password = Column('password', Unicode(60))
    """a hash"""
    last_password_change = Column(
        DateTime,
        default=func.current_timestamp())
    """timestamp of last password change/form submission (Datetime)"""
    email = Column(Unicode(255))
    """email address (Unicode)"""
    groups = relationship(
        Group,
        secondary=staff_groups,
        backref="staff")
    """list of group objects (users groups) (relation)"""
    def _init_(self, login, password, email):  # pragma: no cover
        """
        make new group
        """
        self.login = login
        self.password = password
        self.last_password_change = datetime.now()
        self.email = email

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = hash_password(password)

    password = property(_get_password, _set_password)
    password = synonym('_password', descriptor=password)

    @classmethod
    def get_by_id(cls, staff_id):
        """
        Get C3sStaff object by id.

        Args:
            id: the id of the C3sStaff object to be returned.

        Returns:
            * **object**: C3sStaff object with relevant id, if exists.
            * **None**: if id can't be found.
        """
        return DBSession.query(cls).filter(cls.id == staff_id).first()

    @classmethod
    def get_by_login(cls, login):
        """
        Get C3sStaff object by login.

        Args:
            login: the login of the C3sStaff object to be returned.

        Returns:
            * **object**: C3sStaff object with relevant login, if exists.
            * **None**: if login can't be found.
        """
        return DBSession.query(cls).filter(cls.login == login).first()

    @classmethod
    def check_password(cls, login, password):
        """
        Check staff password.

        Args:
            login: staff login.
            password: staff password as supplied.

        Returns:
            the answer of bcrypt.crypt, comparing the password supplied
                and the hash from the database
        """
        staffer = cls.get_by_login(login)
        return CRYPT.check(staffer.password, password)

    # this one is used by RequestWithUserAttribute
    @classmethod
    def check_user_or_none(cls, login):
        """
        Check whether a user by that login exists in the database.

        Args:
            login: the name to log in with

        Returns:
            * **C3sStaff object**, if login exists.
            * **None**, if login does not exist.
        """
        login = cls.get_by_login(login)  # is None if user not exists
        return login

    @classmethod
    def delete_by_id(cls, staff_id):
        """
        Delete one C3sStaff object by id.
        """
        row = DBSession.query(cls).filter(cls.id == staff_id).first()
        row.groups = []
        DBSession.query(cls).filter(cls.id == staff_id).delete()

    @classmethod
    def get_all(cls):
        """
        Get all C3sStaff objects from the database.

        Returns:
            list: list of C3sStaff objects.
        """
        return DBSession.query(cls).all()


class Shares(Base):
    """
    A package of shares which a member acquires.

    Each shares package consists of one to sixty shares. One member may own
    several packages, e.g. from membership application, crowdfunding and
    requesting the acquisition of additional shares.

    Shares packages only come to existence once the business process is finished
    and the transaction is completed. Information about ongoing processes cannot
    here.
    """
    __tablename__ = 'shares'
    # pylint: disable=invalid-name
    id = Column(Integer, primary_key=True)
    """Technical primary key of the shares package."""
    number = Column(Integer())
    """Number of shares of the shares package."""
    date_of_acquisition = Column(Date(), nullable=False)
    """Date of acquisition of the shares package, i.e. the date of approval of
    the administrative board."""
    reference_code = Column(Unicode(255), unique=True)
    """A reference code used for email confirmation and as bank transfer
    purpose."""
    signature_received = Column(Boolean, default=False)
    """Flag indicating whether the signed application for becoming a member or
    acquiring additional shares was received."""
    signature_received_date = Column(
        Date(), default=date(1970, 1, 1))
    """Date on which the signed application for becoming a member or acquiring
    additional sharess was received."""
    signature_confirmed = Column(Boolean, default=False)
    """Flag indicating whether the confirmation email about the arrival of the
    signed application was sent."""
    signature_confirmed_date = Column(
        Date(), default=date(1970, 1, 1))
    """Date on which the confirmation email about the arrival of the signed
    application was sent."""
    payment_received = Column(Boolean, default=False)
    """Flag indicating whether the payment for the shares package was
    received."""
    payment_received_date = Column(
        Date(), default=date(1970, 1, 1))
    """Date on which the payment for the shares package was received."""
    payment_confirmed = Column(Boolean, default=False)
    """Flag indicating whether the confirmation email about the arrival of the
    payment was sent."""
    payment_confirmed_date = Column(
        Date(), default=date(1970, 1, 1))
    """Date on which the confirmation email about the arrival of the payment was
    sent."""
    accountant_comment = Column(Unicode(255))
    """A free text comment for accounting purposes."""


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
    # invitations
    email_invite_flag_bcgv14 = Column(Boolean, default=False)
    email_invite_date_bcgv14 = Column(DateTime(), default=datetime(1970, 1, 1))
    email_invite_flag_bcgv15 = Column(Boolean, default=False)
    email_invite_date_bcgv15 = Column(DateTime(), default=datetime(1970, 1, 1))
    email_invite_token_bcgv15 = Column(Unicode(255))
    email_invite_flag_bcgv16 = Column(Boolean, default=False)
    email_invite_date_bcgv16 = Column(DateTime(), default=datetime(1970, 1, 1))
    email_invite_token_bcgv16 = Column(Unicode(255))
    email_invite_flag_bcgv17 = Column(Boolean, default=False)
    email_invite_date_bcgv17 = Column(DateTime(), default=datetime(1970, 1, 1))
    email_invite_token_bcgv17 = Column(Unicode(255))
    email_invite_flag_bcgv18 = Column(Boolean, default=False)
    email_invite_date_bcgv18 = Column(DateTime(), default=datetime(1970, 1, 1))
    email_invite_token_bcgv18 = Column(Unicode(255))
    # legal entities
    is_legalentity = Column(Boolean, default=False)
    court_of_law = Column(Unicode(255))
    registration_number = Column(Unicode(255))
    # membership certificate
    certificate_email = Column(Boolean, default=False)
    certificate_token = Column(Unicode(10))
    certificate_email_date = Column(DateTime())

    # membership dues for 2015
    dues15_invoice = Column(Boolean, default=False)  # sent?
    dues15_invoice_date = Column(DateTime())  # when?
    dues15_invoice_no = Column(Integer())  # lfd. nummer
    dues15_token = Column(Unicode(10))  # access token
    dues15_start = Column(Unicode(255))  # a string, 2015 quarter of membership
    dues15_amount = Column(  # calculated amount member has to pay by default
        DatabaseDecimal(12, 2), default=Decimal('NaN'))
    dues15_reduced = Column(Boolean, default=False)  # was reduced?
    _dues15_amount_reduced = Column(
        'dues15_amount_reduced',  # the amount reduced to
        DatabaseDecimal(12, 2), default=Decimal('NaN'))  # ..to xs
    # balance
    _dues15_balance = Column(
        'dues15_balance',  # the amount to be settled
        DatabaseDecimal(12, 2), default=Decimal('0'))
    dues15_balanced = Column(Boolean, default=True)  # was balanced?
    # payment
    dues15_paid = Column(Boolean, default=False)  # payment flag
    dues15_amount_paid = Column(  # how much paid?
        DatabaseDecimal(12, 2), default=Decimal('0'))
    dues15_paid_date = Column(DateTime())  # paid when?

    # membership dues for 2016
    dues16_invoice = Column(Boolean, default=False)  # sent?
    dues16_invoice_date = Column(DateTime())  # when?
    dues16_invoice_no = Column(Integer())  # lfd. nummer
    dues16_token = Column(Unicode(10))  # access token
    dues16_start = Column(Unicode(255))  # a string, 2016 quarter of membership
    dues16_amount = Column(  # calculated amount member has to pay by default
        DatabaseDecimal(12, 2), default=Decimal('NaN'))
    dues16_reduced = Column(Boolean, default=False)  # was reduced?
    _dues16_amount_reduced = Column(
        'dues16_amount_reduced',  # the amount reduced to
        DatabaseDecimal(12, 2), default=Decimal('NaN'))  # ..to xs
    # balance
    _dues16_balance = Column(
        'dues16_balance',  # the amount to be settled
        DatabaseDecimal(12, 2), default=Decimal('0'))
    dues16_balanced = Column(Boolean, default=True)  # was balanced?
    # payment
    dues16_paid = Column(Boolean, default=False)  # payment flag
    dues16_amount_paid = Column(  # how much paid?
        DatabaseDecimal(12, 2), default=Decimal('0'))
    dues16_paid_date = Column(DateTime())  # paid when?

    # membership dues for 2017
    dues17_invoice = Column(Boolean, default=False)  # sent?
    dues17_invoice_date = Column(DateTime())  # when?
    dues17_invoice_no = Column(Integer())  # lfd. nummer
    dues17_token = Column(Unicode(10))  # access token
    dues17_start = Column(Unicode(255))  # a string, 2017 quarter of membership
    dues17_amount = Column(  # calculated amount member has to pay by default
        DatabaseDecimal(12, 2), default=Decimal('NaN'))
    dues17_reduced = Column(Boolean, default=False)  # was reduced?
    _dues17_amount_reduced = Column(
        'dues17_amount_reduced',  # the amount reduced to
        DatabaseDecimal(12, 2), default=Decimal('NaN'))  # ..to xs
    # balance
    _dues17_balance = Column(
        'dues17_balance',  # the amount to be settled
        DatabaseDecimal(12, 2), default=Decimal('0'))
    dues17_balanced = Column(Boolean, default=True)  # was balanced?
    # payment
    dues17_paid = Column(Boolean, default=False)  # payment flag
    dues17_amount_paid = Column(  # how much paid?
        DatabaseDecimal(12, 2), default=Decimal('0'))
    dues17_paid_date = Column(DateTime())  # paid when?

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
            self.name_of_colsoc = u''

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = hash_password(password)

    password = property(_get_password, _set_password)
    password = synonym('_password', descriptor=password)

    @hybrid_property
    def dues15_balance(self):
        """
        TODO: write this docstring
        TODO: write testcase in test_models.py
        """
        return self._dues15_balance

    @dues15_balance.setter
    def dues15_balance(self, dues15_balance):
        """
        TODO: write this docstring
        TODO: write testcase in test_models.py
        """
        self._dues15_balance = dues15_balance
        self.dues15_balanced = self._dues15_balance == Decimal('0')

    @hybrid_property
    def dues15_amount_reduced(self):
        """
        TODO: write this docstring
        TODO: write testcase in test_models.py
        """
        return self._dues15_amount_reduced

    @dues15_amount_reduced.setter
    def dues15_amount_reduced(self, dues15_amount_reduced):
        """
        TODO: write this docstring
        TODO: write testcase in test_models.py
        """
        self._dues15_amount_reduced = dues15_amount_reduced
        self.dues15_reduced = (
            not math.isnan(self.dues15_amount_reduced)
            and
            self.dues15_amount_reduced != self.dues15_amount)

    @hybrid_property
    def dues16_balance(self):
        """
        TODO: write this docstring
        TODO: write testcase in test_models.py
        """
        return self._dues16_balance

    @dues16_balance.setter
    def dues16_balance(self, dues16_balance):
        """
        TODO: write this docstring
        TODO: write testcase in test_models.py
        """
        self._dues16_balance = dues16_balance
        self.dues16_balanced = self._dues16_balance == Decimal('0')

    @hybrid_property
    def dues16_amount_reduced(self):
        """
        TODO: write this docstring
        TODO: write testcase in test_models.py
        """
        return self._dues16_amount_reduced

    @dues16_amount_reduced.setter
    def dues16_amount_reduced(self, dues16_amount_reduced):
        """
        TODO: write this docstring
        TODO: write testcase in test_models.py
        """
        self._dues16_amount_reduced = dues16_amount_reduced
        self.dues16_reduced = \
            not math.isnan(self.dues16_amount_reduced) \
            and \
            self.dues16_amount_reduced != self.dues16_amount

    @hybrid_property
    def dues17_balance(self):
        """
        TODO: write this docstring
        TODO: write testcase in test_models.py
        """
        return self._dues17_balance

    @dues17_balance.setter
    def dues17_balance(self, dues17_balance):
        """
        TODO: write this docstring
        TODO: write testcase in test_models.py
        """
        self._dues17_balance = dues17_balance
        self.dues17_balanced = self._dues17_balance == Decimal('0')

    @hybrid_property
    def dues17_amount_reduced(self):
        """
        TODO: write this docstring
        TODO: write testcase in test_models.py
        """
        return self._dues17_amount_reduced

    @dues17_amount_reduced.setter
    def dues17_amount_reduced(self, dues17_amount_reduced):
        """
        TODO: write this docstring
        TODO: write testcase in test_models.py
        """
        self._dues17_amount_reduced = dues17_amount_reduced
        self.dues17_reduced = \
            not math.isnan(self.dues17_amount_reduced) \
            and \
            self.dues17_amount_reduced != self.dues17_amount

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

    # used got barcamp & general assembly invitations
    @classmethod
    def get_by_bcgvtoken(cls, token):
        """
        Find a member by token used for GA and BarCamp.

        This is needed when a user returns from reading her email
        and clicking on a link containing the token.

        Returns:
            object: C3sMember object
        """
        return DBSession.query(cls).filter(
            cls.email_invite_token_bcgv18 == token).first()

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
    def get_by_dues15_token(cls, code):
        """return one member by fee token"""
        return DBSession.query(cls).filter(cls.dues15_token == code).first()

    @classmethod
    def get_by_dues16_token(cls, code):
        """return one member by fee token"""
        return DBSession.query(cls).filter(cls.dues16_token == code).first()

    @classmethod
    def get_by_dues17_token(cls, code):
        """return one member by fee token"""
        return DBSession.query(cls).filter(cls.dues17_token == code).first()

    @classmethod
    def get_all(cls):
        """return all afms and members"""
        return DBSession.query(cls).all()

    # needed for invitation to barcam & general assembly
    @classmethod
    def get_invitees(cls, num):
        """
        Get a given number *n* of members to invite for barcamp and GV.

        Queries the database for members, where

        * members are accepted
        * members have not received their invitation email yet

        Args:
          num is the number *n* of invitees to return

        Returns:
          a list of *n* member objects
        """
        return DBSession.query(cls).filter(
            and_(
                cls.is_member_filter(),
                or_(
                    (cls.email_invite_flag_bcgv18 == 0),
                    (cls.email_invite_flag_bcgv18 == ''),
                    # pylint: disable=singleton-comparison
                    (cls.email_invite_flag_bcgv18 == None),
                )
            )
        ).slice(0, num).all()

    @classmethod
    def get_dues15_invoicees(cls, num):
        """
        Get a given number *n* of members to send dues invoices to.

        Queries the database for members, where

        * members are accepted
        * members have not received their dues invoice email yet

        Args:
          num is the number *n* of C3sMembers to return

        Returns:
          a list of *n* member objects
        """
        return DBSession.query(cls).filter(
            and_(
                cls.membership_accepted == 1,
                cls.dues15_invoice == 0
            )).slice(0, num).all()

    @classmethod
    def get_dues16_invoicees(cls, num):
        """
        Get a given number *n* of members to send dues invoices to.

        Queries the database for members, where

        * members are accepted
        * members have not received their dues invoice email yet

        Args:
          num is the number *n* of C3sMembers to return

        Returns:
          a list of *n* member objects
        """
        return DBSession.query(cls).filter(
            and_(
                cls.membership_accepted == 1,
                cls.dues16_invoice == 0,
                cls.membership_date < date(2017, 1, 1),
                cls.membership_type.in_([u'normal', u'investing'])
            )).slice(0, num).all()

    @classmethod
    def get_dues17_invoicees(cls, num):
        """
        Get a given number *n* of members to send dues invoices to.

        Queries the database for members, where

        * members are accepted
        * members have not received their dues invoice email yet

        Args:
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
                cls.dues17_invoice == False,
                cls.membership_date < date(2018, 1, 1),
                cls.membership_type.in_([u'normal', u'investing']),
                or_(
                    cls.membership_loss_date == None,
                    cls.membership_loss_date >= date(2017, 1, 1),
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
                print("exception at id {}: {}".format(
                    row.id,
                    row.postcode))
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
            cls.membership_type == u'normal'
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
            cls.membership_type == u'investing'
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
            cls.membership_type != u'normal',
            cls.membership_type != u'investing'
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
        return CRYPT.check(member.password, password)

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
            if row.country not in countries.keys():
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

    def set_dues15_payment(self, paid_amount, paid_date):
        if math.isnan(self.dues15_amount_paid):
            dues15_amount_paid = Decimal('0')
        else:
            dues15_amount_paid = self.dues15_amount_paid

        self.dues15_paid = True
        self.dues15_amount_paid = dues15_amount_paid + paid_amount
        self.dues15_paid_date = paid_date
        self.dues15_balance = self.dues15_balance - paid_amount

    def set_dues15_amount(self, dues_amount):
        if math.isnan(self.dues15_amount):
            dues15_amount = Decimal('0')
        else:
            dues15_amount = self.dues15_amount

        self.dues15_balance = self.dues15_balance - dues15_amount + Decimal(
            dues_amount)  # what they actually have to pay
        self.dues15_amount = dues_amount  # what they have to pay (calc'ed)

    def set_dues15_reduced_amount(self, reduced_amount):
        if reduced_amount != self.dues15_amount:
            previous_amount_in_balance = (
                self.dues15_amount_reduced
                if self.dues15_reduced
                else self.dues15_amount)
            self.dues15_balance = self.dues15_balance - \
                previous_amount_in_balance + reduced_amount
            self.dues15_amount_reduced = reduced_amount
        else:
            self.dues15_amount_reduced = Decimal('NaN')

    def set_dues16_payment(self, paid_amount, paid_date):
        if math.isnan(self.dues16_amount_paid):
            dues16_amount_paid = Decimal('0')
        else:
            dues16_amount_paid = self.dues16_amount_paid

        self.dues16_paid = True
        self.dues16_amount_paid = dues16_amount_paid + paid_amount
        self.dues16_paid_date = paid_date
        self.dues16_balance = self.dues16_balance - paid_amount

    def set_dues16_amount(self, dues_amount):
        if math.isnan(self.dues16_amount):
            dues16_amount = Decimal('0')
        else:
            dues16_amount = self.dues16_amount

        self.dues16_balance = self.dues16_balance - dues16_amount + Decimal(
            dues_amount)  # what they actually have to pay
        self.dues16_amount = dues_amount  # what they have to pay (calc'ed)

    def set_dues16_reduced_amount(self, reduced_amount):
        if reduced_amount != self.dues16_amount:
            previous_amount_in_balance = (
                self.dues16_amount_reduced
                if self.dues16_reduced
                else self.dues16_amount)
            self.dues16_balance = self.dues16_balance - \
                previous_amount_in_balance + reduced_amount
            self.dues16_amount_reduced = reduced_amount
        else:
            self.dues16_amount_reduced = Decimal('NaN')

    def set_dues17_payment(self, paid_amount, paid_date):
        if math.isnan(self.dues17_amount_paid):
            dues17_amount_paid = Decimal('0')
        else:
            dues17_amount_paid = self.dues17_amount_paid

        self.dues17_paid = True
        self.dues17_amount_paid = dues17_amount_paid + paid_amount
        self.dues17_paid_date = paid_date
        self.dues17_balance = self.dues17_balance - paid_amount

    def set_dues17_amount(self, dues_amount):
        if math.isnan(self.dues17_amount):
            dues17_amount = Decimal('0')
        else:
            dues17_amount = self.dues17_amount

        self.dues17_balance = self.dues17_balance - dues17_amount + Decimal(
            dues_amount)  # what they actually have to pay
        self.dues17_amount = dues_amount  # what they have to pay (calc'ed)

    def set_dues17_reduced_amount(self, reduced_amount):
        if reduced_amount != self.dues17_amount:
            previous_amount_in_balance = (
                self.dues17_amount_reduced
                if self.dues17_reduced
                else self.dues17_amount)
            self.dues17_balance = self.dues17_balance - \
                previous_amount_in_balance + reduced_amount
            self.dues17_amount_reduced = reduced_amount
        else:
            self.dues17_amount_reduced = Decimal('NaN')

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



class Dues15Invoice(Base):
    """
    This table stores the invoices for the 2015 version of dues.

    We need this for bookkeeping,
    because whenever a member is granted a reduction of her dues,
    the old invoice is canceled by a reversal invoice
    and a new invoice must be issued.

    Edge case: if reduced to 0, no new invoice needed.

    """
    __tablename__ = 'dues15invoices'
    # pylint: disable=invalid-name
    id = Column(Integer, primary_key=True)
    """tech. id. / no. in table (integer, primary key)"""
    # this invoice
    invoice_no = Column(Integer(), unique=True)
    """invoice number (Integer, unique)"""
    invoice_no_string = Column(Unicode(255), unique=True)
    """invoice number string (unique)"""
    invoice_date = Column(DateTime())
    """timestamp of invoice creation (DateTime)"""
    invoice_amount = Column(DatabaseDecimal(12, 2), default=Decimal('NaN'))
    """amount (DatabaseDecimal(12,2))"""
    # has it been superseeded by reversal?
    is_cancelled = Column(Boolean, default=False)
    """flag: invoice has been superseeded by reversal or cancellation"""
    cancelled_date = Column(DateTime())
    """timestamp of cancellation/reversal"""
    # is it a reversal?
    is_reversal = Column(Boolean, default=False)
    """flag: is this a reversal invoice?"""
    # is it a reduction (or even more than default)?
    is_altered = Column(Boolean, default=False)
    """flag: has the amount been reduced or increased?"""
    # person reference
    member_id = Column(Integer())
    """reference to C3sMember id"""
    membership_no = Column(Integer())
    """reference to C3sMember membership_number"""
    email = Column(Unicode(255))
    """C3sMembers email we sent this invoice to"""
    token = Column(Unicode(255))
    """used to limit access to this invoice"""
    # referrals
    preceding_invoice_no = Column(Integer(), default=None)
    """the invoice number preceeding this one, if applicable"""
    succeeding_invoice_no = Column(Integer(), default=None)
    """the invoice number succeeding this one, if applicable"""

    def __init__(
            self,
            invoice_no,
            invoice_no_string,
            invoice_date,
            invoice_amount,
            member_id,
            membership_no,
            email,
            token):
        """
        Make a new invoice object

        Args:
            invoice_no: invoice number
            invoice_no_string: invoice number string
            invoice_date: timestamp of creation
            invoice_amount: amount of money
            member_id: references C3sMember
            membership_no: references C3sMember
            email: email to send it to
            token: a token to limit access
        """
        self.invoice_no = invoice_no
        self.invoice_no_string = invoice_no_string
        self.invoice_date = invoice_date
        self.invoice_amount = invoice_amount
        self.member_id = member_id
        self.membership_no = membership_no
        self.email = email
        self.token = token

    @classmethod
    def get_all(cls):
        """
        Return all dues15 invoices
        """
        return DBSession.query(cls).all()

    @classmethod
    def get_by_invoice_no(cls, number):
        """return one invoice by invoice number"""
        return DBSession.query(cls).filter(cls.invoice_no == number).first()

    @classmethod
    def get_by_membership_no(cls, number):
        """return all invoices of one member by membership number"""
        return DBSession.query(cls).filter(cls.membership_no == number).all()

    @classmethod
    def get_max_invoice_no(cls):
        """
        Get the maximum invoice number.

        Returns:
            * Integer: maximum of given invoice numbers or 0"""
        res, = DBSession.query(func.max(cls.id)).first()

        if res is None:
            return 0
        return res

    @classmethod
    def check_for_existing_dues15_token(cls, dues_token):
        """
        Check if a dues token is already present.

        Args:
            dues_token: a given string

        Returns:
            * **True**, if token already in table
            * **False** else
        """
        check = DBSession.query(cls).filter(
            cls.token == dues_token).first()
        return check is not None

    @classmethod
    def get_monthly_stats(cls):
        """
        Gets the monthly statistics.

        Provides sums of the normale as well as reversal invoices per
        calendar month based on the invoice date.
        """
        result = []
        # SQLite specific: substring for SQLite as it does not support
        # date_trunc.
        # invoice_date_month = func.date_trunc(
        #     'month',
        #     Dues15Invoice.invoice_date)
        invoice_date_month = func.substr(Dues15Invoice.invoice_date, 1, 7)
        payment_date_month = func.substr(C3sMember.dues15_paid_date, 1, 7)

        # collect the invoice amounts per month
        invoice_amounts_query = DBSession.query(
            invoice_date_month.label('month'),
            func.sum(expression.case(
                [(
                    expression.not_(Dues15Invoice.is_reversal),
                    Dues15Invoice.invoice_amount)],
                else_=Decimal('0.0'))).label('amount_invoiced_normal'),
            func.sum(expression.case(
                [(
                    Dues15Invoice.is_reversal,
                    Dues15Invoice.invoice_amount)],
                else_=Decimal('0.0'))).label('amount_invoiced_reversal'),
            expression.literal_column(
                '\'0.0\'', SqliteDecimal).label('amount_paid')
        ).group_by(invoice_date_month)
        # collect the payments per month
        member_payments_query = DBSession.query(
            payment_date_month.label('month'),
            expression.literal_column(
                '\'0.0\'', SqliteDecimal).label('amount_invoiced_normal'),
            expression.literal_column(
                '\'0.0\'', SqliteDecimal
            ).label('amount_invoiced_reversal'),
            func.sum(C3sMember.dues15_amount_paid).label('amount_paid')
        ).filter(C3sMember.dues15_paid_date.isnot(None)) \
            .group_by(payment_date_month)
        # union invoice amounts and payments
        union_all_query = expression.union_all(
            member_payments_query, invoice_amounts_query)
        # aggregate invoice amounts and payments by month
        result_query = DBSession.query(
            union_all_query.c.month.label('month'),
            func.sum(union_all_query.c.amount_invoiced_normal).label(
                'amount_invoiced_normal'),
            func.sum(union_all_query.c.amount_invoiced_reversal).label(
                'amount_invoiced_reversal'),
            func.sum(union_all_query.c.amount_paid).label('amount_paid')
        ) \
            .group_by(union_all_query.c.month) \
            .order_by(union_all_query.c.month)
        for month_stat in result_query.all():
            result.append(
                {
                    'month': datetime(
                        int(month_stat[0][0:4]),
                        int(month_stat[0][5:7]),
                        1),
                    'amount_invoiced_normal': month_stat[1],
                    'amount_invoiced_reversal': month_stat[2],
                    'amount_paid': month_stat[3]
                })
        return result

class Dues16Invoice(Base):
    """
    This table stores the invoices for the 2015 version of dues.

    We need this for bookkeeping,
    because whenever a member is granted a reduction of her dues,
    the old invoice is canceled by a reversal invoice
    and a new invoice must be issued.

    Edge case: if reduced to 0, no new invoice needed.

    """
    __tablename__ = 'dues16invoices'
    # pylint: disable=invalid-name
    id = Column(Integer, primary_key=True)
    """tech. id. / no. in table (integer, primary key)"""
    # this invoice
    invoice_no = Column(Integer(), unique=True)
    """invoice number (Integer, unique)"""
    invoice_no_string = Column(Unicode(255), unique=True)
    """invoice number string (unique)"""
    invoice_date = Column(DateTime())
    """timestamp of invoice creation (DateTime)"""
    invoice_amount = Column(DatabaseDecimal(12, 2), default=Decimal('NaN'))
    """amount (DatabaseDecimal(12,2))"""
    # has it been superseeded by reversal?
    is_cancelled = Column(Boolean, default=False)
    """flag: invoice has been superseeded by reversal or cancellation"""
    cancelled_date = Column(DateTime())
    """timestamp of cancellation/reversal"""
    # is it a reversal?
    is_reversal = Column(Boolean, default=False)
    """flag: is this a reversal invoice?"""
    # is it a reduction (or even more than default)?
    is_altered = Column(Boolean, default=False)
    """flag: has the amount been reduced or increased?"""
    # person reference
    member_id = Column(Integer())
    """reference to C3sMember id"""
    membership_no = Column(Integer())
    """reference to C3sMember membership_number"""
    email = Column(Unicode(255))
    """C3sMembers email we sent this invoice to"""
    token = Column(Unicode(255))
    """used to limit access to this invoice"""
    # referrals
    preceding_invoice_no = Column(Integer(), default=None)
    """the invoice number preceeding this one, if applicable"""
    succeeding_invoice_no = Column(Integer(), default=None)
    """the invoice number succeeding this one, if applicable"""

    def __init__(
            self,
            invoice_no,
            invoice_no_string,
            invoice_date,
            invoice_amount,
            member_id,
            membership_no,
            email,
            token):
        """
        Make a new invoice object

        Args:
            invoice_no: invoice number
            invoice_no_string: invoice number string
            invoice_date: timestamp of creation
            invoice_amount: amount of money
            member_id: references C3sMember
            membership_no: references C3sMember
            email: email to send it to
            token: a token to limit access
        """
        self.invoice_no = invoice_no
        self.invoice_no_string = invoice_no_string
        self.invoice_date = invoice_date
        self.invoice_amount = invoice_amount
        self.member_id = member_id
        self.membership_no = membership_no
        self.email = email
        self.token = token

    @classmethod
    def get_all(cls):
        """
        Return all dues16 invoices
        """
        return DBSession.query(cls).all()

    @classmethod
    def get_by_invoice_no(cls, _no):
        """return one invoice by invoice number"""
        return DBSession.query(cls).filter(cls.invoice_no == _no).first()

    @classmethod
    def get_by_membership_no(cls, _no):
        """return all invoices of one member by membership number"""
        return DBSession.query(cls).filter(cls.membership_no == _no).all()

    @classmethod
    def get_max_invoice_no(cls):
        """
        Get the maximum invoice number.

        Returns:
            * Integer: maximum of given invoice numbers or 0"""
        res, = DBSession.query(func.max(cls.id)).first()

        if res is None:
            return 0
        return res

    @classmethod
    def check_for_existing_dues16_token(cls, dues_token):
        """
        Check if a dues token is already present.

        Args:
            dues_token: a given string

        Returns:
            * **True**, if token already in table
            * **False** else
        """
        check = DBSession.query(cls).filter(
            cls.token == dues_token).first()
        return check is not None

    @classmethod
    def get_monthly_stats(cls):
        """
        Gets the monthly statistics.

        Provides sums of the normale as well as reversal invoices per
        calendar month based on the invoice date.
        """
        result = []
        # SQLite specific: substring for SQLite as it does not support
        # date_trunc.
        # invoice_date_month = func.date_trunc(
        #     'month',
        #     Dues16Invoice.invoice_date)
        invoice_date_month = func.substr(Dues16Invoice.invoice_date, 1, 7)
        payment_date_month = func.substr(C3sMember.dues16_paid_date, 1, 7)

        # collect the invoice amounts per month
        invoice_amounts_query = DBSession.query(
            invoice_date_month.label('month'),
            func.sum(expression.case(
                [(
                    expression.not_(Dues16Invoice.is_reversal),
                    Dues16Invoice.invoice_amount)],
                else_=Decimal('0.0'))).label('amount_invoiced_normal'),
            func.sum(expression.case(
                [(
                    Dues16Invoice.is_reversal,
                    Dues16Invoice.invoice_amount)],
                else_=Decimal('0.0'))).label('amount_invoiced_reversal'),
            expression.literal_column(
                '\'0.0\'', SqliteDecimal).label('amount_paid')
        ).group_by(invoice_date_month)
        # collect the payments per month
        member_payments_query = DBSession.query(
            payment_date_month.label('month'),
            expression.literal_column(
                '\'0.0\'', SqliteDecimal).label('amount_invoiced_normal'),
            expression.literal_column(
                '\'0.0\'', SqliteDecimal
            ).label('amount_invoiced_reversal'),
            func.sum(C3sMember.dues16_amount_paid).label('amount_paid')
        ).filter(C3sMember.dues16_paid_date.isnot(None)) \
            .group_by(payment_date_month)
        # union invoice amounts and payments
        union_all_query = expression.union_all(
            member_payments_query, invoice_amounts_query)
        # aggregate invoice amounts and payments by month
        result_query = DBSession.query(
            union_all_query.c.month.label('month'),
            func.sum(union_all_query.c.amount_invoiced_normal).label(
                'amount_invoiced_normal'),
            func.sum(union_all_query.c.amount_invoiced_reversal).label(
                'amount_invoiced_reversal'),
            func.sum(union_all_query.c.amount_paid).label('amount_paid')
        ) \
            .group_by(union_all_query.c.month) \
            .order_by(union_all_query.c.month)
        for month_stat in result_query.all():
            result.append(
                {
                    'month': datetime(
                        int(month_stat[0][0:4]),
                        int(month_stat[0][5:7]),
                        1),
                    'amount_invoiced_normal': month_stat[1],
                    'amount_invoiced_reversal': month_stat[2],
                    'amount_paid': month_stat[3]
                })
        return result

class Dues17Invoice(Base):
    """
    This table stores the invoices for the 2015 version of dues.

    We need this for bookkeeping,
    because whenever a member is granted a reduction of her dues,
    the old invoice is canceled by a reversal invoice
    and a new invoice must be issued.

    Edge case: if reduced to 0, no new invoice needed.

    """
    __tablename__ = 'dues17invoices'
    # pylint: disable=invalid-name
    id = Column(Integer, primary_key=True)
    """tech. id. / no. in table (integer, primary key)"""
    # this invoice
    invoice_no = Column(Integer(), unique=True)
    """invoice number (Integer, unique)"""
    invoice_no_string = Column(Unicode(255), unique=True)
    """invoice number string (unique)"""
    invoice_date = Column(DateTime())
    """timestamp of invoice creation (DateTime)"""
    invoice_amount = Column(DatabaseDecimal(12, 2), default=Decimal('NaN'))
    """amount (DatabaseDecimal(12,2))"""
    # has it been superseeded by reversal?
    is_cancelled = Column(Boolean, default=False)
    """flag: invoice has been superseeded by reversal or cancellation"""
    cancelled_date = Column(DateTime())
    """timestamp of cancellation/reversal"""
    # is it a reversal?
    is_reversal = Column(Boolean, default=False)
    """flag: is this a reversal invoice?"""
    # is it a reduction (or even more than default)?
    is_altered = Column(Boolean, default=False)
    """flag: has the amount been reduced or increased?"""
    # person reference
    member_id = Column(Integer())
    """reference to C3sMember id"""
    membership_no = Column(Integer())
    """reference to C3sMember membership_number"""
    email = Column(Unicode(255))
    """C3sMembers email we sent this invoice to"""
    token = Column(Unicode(255))
    """used to limit access to this invoice"""
    # referrals
    preceding_invoice_no = Column(Integer(), default=None)
    """the invoice number preceeding this one, if applicable"""
    succeeding_invoice_no = Column(Integer(), default=None)
    """the invoice number succeeding this one, if applicable"""

    def __init__(
            self,
            invoice_no,
            invoice_no_string,
            invoice_date,
            invoice_amount,
            member_id,
            membership_no,
            email,
            token):
        """
        Make a new invoice object

        Args:
            invoice_no: invoice number
            invoice_no_string: invoice number string
            invoice_date: timestamp of creation
            invoice_amount: amount of money
            member_id: references C3sMember
            membership_no: references C3sMember
            email: email to send it to
            token: a token to limit access
        """
        self.invoice_no = invoice_no
        self.invoice_no_string = invoice_no_string
        self.invoice_date = invoice_date
        self.invoice_amount = invoice_amount
        self.member_id = member_id
        self.membership_no = membership_no
        self.email = email
        self.token = token

    @classmethod
    def get_all(cls):
        """
        Return all dues17 invoices
        """
        return DBSession.query(cls).all()

    @classmethod
    def get_by_invoice_no(cls, _no):
        """return one invoice by invoice number"""
        return DBSession.query(cls).filter(cls.invoice_no == _no).first()

    @classmethod
    def get_by_membership_no(cls, _no):
        """return all invoices of one member by membership number"""
        return DBSession.query(cls).filter(cls.membership_no == _no).all()

    @classmethod
    def get_max_invoice_no(cls):
        """
        Get the maximum invoice number.

        Returns:
            * Integer: maximum of given invoice numbers or 0"""
        res, = DBSession.query(func.max(cls.id)).first()

        if res is None:
            return 0
        return res

    @classmethod
    def check_for_existing_dues17_token(cls, dues_token):
        """
        Check if a dues token is already present.

        Args:
            dues_token: a given string

        Returns:
            * **True**, if token already in table
            * **False** else
        """
        check = DBSession.query(cls).filter(
            cls.token == dues_token).first()
        return check is not None

    @classmethod
    def get_monthly_stats(cls):
        """
        Gets the monthly statistics.

        Provides sums of the normale as well as reversal invoices per
        calendar month based on the invoice date.
        """
        result = []
        # SQLite specific: substring for SQLite as it does not support
        # date_trunc.
        # invoice_date_month = func.date_trunc(
        #     'month',
        #     Dues17Invoice.invoice_date)
        invoice_date_month = func.substr(Dues17Invoice.invoice_date, 1, 7)
        payment_date_month = func.substr(C3sMember.dues17_paid_date, 1, 7)

        # collect the invoice amounts per month
        invoice_amounts_query = DBSession.query(
            invoice_date_month.label('month'),
            func.sum(expression.case(
                [(
                    expression.not_(Dues17Invoice.is_reversal),
                    Dues17Invoice.invoice_amount)],
                else_=Decimal('0.0'))).label('amount_invoiced_normal'),
            func.sum(expression.case(
                [(
                    Dues17Invoice.is_reversal,
                    Dues17Invoice.invoice_amount)],
                else_=Decimal('0.0'))).label('amount_invoiced_reversal'),
            expression.literal_column(
                '\'0.0\'', SqliteDecimal).label('amount_paid')
        ).group_by(invoice_date_month)
        # collect the payments per month
        member_payments_query = DBSession.query(
            payment_date_month.label('month'),
            expression.literal_column(
                '\'0.0\'', SqliteDecimal).label('amount_invoiced_normal'),
            expression.literal_column(
                '\'0.0\'', SqliteDecimal
            ).label('amount_invoiced_reversal'),
            func.sum(C3sMember.dues17_amount_paid).label('amount_paid')
        ).filter(C3sMember.dues17_paid_date.isnot(None)) \
            .group_by(payment_date_month)
        # union invoice amounts and payments
        union_all_query = expression.union_all(
            member_payments_query, invoice_amounts_query)
        # aggregate invoice amounts and payments by month
        result_query = DBSession.query(
            union_all_query.c.month.label('month'),
            func.sum(union_all_query.c.amount_invoiced_normal).label(
                'amount_invoiced_normal'),
            func.sum(union_all_query.c.amount_invoiced_reversal).label(
                'amount_invoiced_reversal'),
            func.sum(union_all_query.c.amount_paid).label('amount_paid')
        ) \
            .group_by(union_all_query.c.month) \
            .order_by(union_all_query.c.month)
        for month_stat in result_query.all():
            result.append(
                {
                    'month': datetime(
                        int(month_stat[0][0:4]),
                        int(month_stat[0][5:7]),
                        1),
                    'amount_invoiced_normal': month_stat[1],
                    'amount_invoiced_reversal': month_stat[2],
                    'amount_paid': month_stat[3]
                })
        return result
