from pyramid.authorization import (
    Allow,
    # Deny,
)
from pyramid.authorization import ALL_PERMISSIONS


def groupfinder(userid, request):
    """
    Find Groups for a user.

    Args:
        userid: the current userid
        request: the current request

    Returns:
        list: strings of group names
    """
    user = request.user
    if user:
        return ['%s' % g for g in user.groups]


# ### MAP GROUPS TO PERMISSIONS
class Root(object):
    """
    This is the Security Root object,
    where groups are given certain permissions.

    see also
    http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/security.html#assigning-acls-to-your-resource-objects

    **__acl__**

    * Access Control List (ACL) consisting of Access Control Entries (ACE)
    """
    __acl__ = [
        (Allow, 'system.Everyone', 'view'),
        (Allow, 'group:staff', ALL_PERMISSIONS),
    ]

    def __init__(self, request):
        self.request = request
