"""
This module holds functionality to administer a members shares.
"""

import logging

import colander
import deform
from deform import ValidationFailure
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from c3smembership.presentation.i18n import _
from c3smembership.presentation.views.membership_listing import (
    get_memberhip_listing_redirect
)

LOG = logging.getLogger(__name__)


@view_config(renderer='templates/shares_detail.pt',
             permission='manage',
             route_name='shares_detail')
def shares_detail(request):
    '''
    Show details about a package of shares.
    '''
    share = request.registry.share_information.get(request.matchdict['id'])
    if share is None:
        # entry was not found in database
        request.session.flash(
            'This shares id was not found in the database!',
            'message_to_staff'
        )
        return HTTPFound(
            request.route_url('toolbox'))

    # get shares owner if possible
    try:
        member_id = share.members[0].id
        member_firstname = share.members[0].firstname
        member_lastname = share.members[0].lastname
    except IndexError:
        member_id = 0
        member_firstname = 'Not'
        member_lastname = 'Found'

    return {
        's': share,  # the share
        'm_id': member_id,  # the owner
        'm_first': member_firstname,  # the owner
        'm_last': member_lastname,  # the owner
    }


@view_config(renderer='templates/shares_edit.pt',
             permission='manage',
             route_name='shares_edit')
def shares_edit(request):
    '''
    Edit details of a package of shares.
    '''
    # load info from DB -- if possible
    share = request.registry.share_information.get(request.matchdict['id'])

    if share is None:
        # entry was not found in database
        return get_memberhip_listing_redirect(request)
    else:
        appstruct = {}
        appstruct = {
            'number': share.number,
            'date_of_acquisition': share.date_of_acquisition,
        }

    # construct a form
    class SharesSchema(colander.Schema):
        """
        Defines the colander schema for shares.
        """
        number = colander.SchemaNode(
            colander.Integer(),
            title=_('Number of Shares'),
        )
        date_of_acquisition = colander.SchemaNode(
            colander.Date(),
            title=_('Date of Acquisition')
        )
    schema = SharesSchema()
    form = deform.Form(
        schema,
        buttons=[deform.Button('submit', _(u'Submit'))],
    )
    # form generation complete

    # if the form has been used and SUBMITTED, check contents
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)

        except ValidationFailure as validation_failure:  # pragma: no cover
            request.session.flash(
                _(u'Please note: There were errors, '
                  'please check the form below.'),
                'message_above_form',
                allow_duplicate=False)
            return{'form': validation_failure.render()}

        # if no error occurred, persist the changed values info in database

        test1 = (  # changed value through form (different from db)?
            appstruct['number'] == share.number)
        if not test1:
            LOG.info(
                'info about number of shares of %s changed by %s to %s',
                share.id,
                request.user.login,
                appstruct['number'])
            share.number = appstruct['number']
        test2 = (  # changed value through form (different from db)?
            appstruct['date_of_acquisition'] == share.date_of_acquisition)
        if not test2:
            LOG.info(
                'info about date_of_acquisition of %s changed by %s to %s',
                share.id,
                request.user.login,
                appstruct['date_of_acquisition'])
            share.date_of_acquisition = appstruct['date_of_acquisition']
        # store appstruct in session
        # request.session['appstruct'] = appstruct

    else:  # no form submission
        # prepopulate form
        form.set_appstruct(appstruct)

    html = form.render()

    return {
        's': share,
        'form': html
    }


@view_config(permission='manage',
             route_name='shares_delete')
def shares_delete(request):
    '''
    Staff may delete a package of shares.
    '''
    shares_id = request.matchdict['id']
    # load info from DB -- if possible
    share = request.registry.share_information.get(shares_id)

    if share is None:
        # entry was not found in database
        request.session.flash(
            'This shares package {} was not found in the DB.'.format(shares_id),
            'message_to_staff'
        )
        return HTTPFound(request.route_url('toolbox'))

    if len(share.members) > 0:
        # shares package is still owned
        request.session.flash(
            'DID NOT DELETE! '
            'This shares package {} still has a member owning it.'.format(
                shares_id),
            'message_to_staff'
        )
        return HTTPFound(request.route_url('toolbox'))
    else:
        request.registry.share_information.delete(shares_id)
        request.session.flash(
            'the shares package {} was deleted.'.format(shares_id),
            'message_to_staff'
        )
        return HTTPFound(request.route_url('toolbox'))
