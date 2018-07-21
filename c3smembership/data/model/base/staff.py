# -*- coding: utf-8  -*-
"""
Staff
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Table,
    Unicode,
)
from sqlalchemy.orm import (
    relationship,
    synonym,
)
from sqlalchemy.sql import func

from c3smembership.data.model.base import (
    Base,
    check_password,
    DBSession,
    hash_password,
)
from c3smembership.data.model.base.group import Group


# pylint: disable=no-member


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

class Staff(Base):
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
        return check_password(staffer.password, password)

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
