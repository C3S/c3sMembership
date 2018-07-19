# -*- coding: utf-8 -*-
"""
This module holds REST API views to interact with c3sPartyTicketing.

When invitations for parties or barcamp and general assembly are sent,
those emails contain links to c3sPartyTicketing aka https://events.c3s.cc.

When a member clicks her link to get a ticket,
the ticketing app queries the membership app to get a members details:

* first name
* last name
* email address
* membership type

=== ====================
URL http/s://app:port/lm
=== ====================

There are two validators involved:

* token_does_exist: îs there a token?
* token_does_match: is the token correct?

"""

from cornice import Service
import json
from types import NoneType
from webob.exc import HTTPUnauthorized

from c3smembership.models import C3sMember

api_ver = '0.1dev'

member = Service(name='member', path='/lm', description="load user info")

DEBUG = False


def auth_header_does_match(request):
    '''
    a validator to check the authentication header
    '''
    _auth_token = request.headers['X-messaging-token']
    if DEBUG:  # pragma: no cover
        print("the api received this: {}".format(_auth_token))
    if ((_auth_token in request.registry.settings['api_auth_token']) and
            (request.registry.settings['api_auth_token'] in _auth_token)):
        pass
        if DEBUG:  # pragma: no cover
            print("validator: token: all good!")
    else:
        request.errors.add('url', 'name', 'AuthToken does not match!')
        raise HTTPUnauthorized()


def token_does_exist(request):
    """
    validator: check existence of token
    """
    req = json.loads(request.body)
    _token = req['token']
    if DEBUG:  # pragma: no cover
        print("the request: {}".format(req))
        print("the token: {}".format(_token))
    request.validated['refcode'] = _token


@member.put(validators=(token_does_exist, auth_header_does_match))
def api_userinfo(request):
    '''
    Allow api access to load user info (for ticketing)
    '''
    if DEBUG:  # pragma: no cover
        print(u"the refcode received: {}".format(request.validated['refcode']))

    _m = C3sMember.get_by_bcgvtoken(request.validated['refcode'])
    if isinstance(_m, NoneType):
        return {
            'firstname': 'None',
            'lastname': 'None',
        }
    # print "api found member: {} {}".format(_m.firstname, _m.lastname)
    return {
        'firstname': _m.firstname,
        'lastname': _m.lastname,
        'email': _m.email,
        'mtype': _m.membership_type,
        'is_legalentity': _m.is_legalentity,
    }
