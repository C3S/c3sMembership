# ### Making A 'User Object' Available as a Request Attribute
# docs.pylonsproject.org/projects/pyramid_cookbook/dev/authentication.html
from pyramid.decorator import reify
from pyramid.request import Request
from pyramid.security import unauthenticated_userid
from c3smembership.data.model.base.staff import Staff


class RequestWithUserAttribute(Request):
    """
    This class is used as replacement for the common Request class.

    It adds an important feature for c3sMembership: a request.user attribute,
    telling who is authenticated and using the app during this request.

    This is useful to protect some views to be used by staff only.
    """
    @reify
    def user(self):
        """
        The request.user attribute.

        Returns:
            * **id**, if user is known.
            * **None**, if user is not known.
        """
        userid = unauthenticated_userid(self)
        # print "--- in RequestWithUserAttribute: userid = " + str(userid)
        if userid is not None:
            # this should return None if the user doesn't exist
            # in the database
            # return dbsession.query('users').filter(user.user_id == userid)
            return Staff.check_user_or_none(userid)
        # else: userid == None
        return userid  # pragma: no cover

# /end of ### Making A 'User Object' Available as a Request Attribute
