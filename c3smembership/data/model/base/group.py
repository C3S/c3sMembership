# -*- coding: utf-8  -*-
"""
Group
"""

from sqlalchemy import (
    Column,
    Integer,
    Unicode,
)

from c3smembership.data.model.base import (
    Base,
    DBSession,
)


class Group(Base):
    # pylint: disable=too-few-public-methods
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
