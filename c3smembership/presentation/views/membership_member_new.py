# -*- coding: utf-8 -*-
"""
This module has functionality for staff to enter new member application
datasets into the database from the backend.
"""

from datetime import (
    date,
    datetime,
)
import random
import string
from types import NoneType

import colander
import deform
from deform import ValidationFailure
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from sqlalchemy.exc import (
    InvalidRequestError,
    IntegrityError
)

from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.presentation.i18n import (
    _,
    ZPT_RENDERER,
)
from c3smembership.presentation.schemas.member import PersonalDataCreateEdit


COUNTRY_DEFAULT = 'Germany'


@view_config(
    route_name='new_member',
    permission='manage',
    renderer='c3smembership.presentation:templates/pages/'
             'membership_member_new.pt')
def new_member(request):
    '''
    Let staff create a new member entry, when receiving input via dead wood
    '''

    class MembershipInfo(colander.Schema):
        """
        Schema for membership specific information
        """

        yes_no = ((u'yes', _(u'Yes')),
                  (u'no', _(u'No')),
                  (u'dontknow', _(u'Unknown')),)

        entity_type = colander.SchemaNode(
            colander.String(),
            title=(u'Person oder Körperschaft?'),
            description=u'Bitte die Kategorie des Mitglied auswählen.',
            widget=deform.widget.RadioChoiceWidget(
                values=(
                    (u'person',
                     (u'Person')),
                    (u'legalentity',
                     u'Körperschaft'),
                ),
            ),
            missing=unicode(''),
            oid='entity_type',
        )
        membership_type = colander.SchemaNode(
            colander.String(),
            title=(u'Art der Mitgliedschaft (lt. Satzung, §4)'),
            description=u'Bitte die Art der Mitgliedschaft auswählen.',
            widget=deform.widget.RadioChoiceWidget(
                values=(
                    (u'normal',
                     (u'Normales Mitglied')),
                    (u'investing',
                     u'Investierendes Mitglied'),
                    (u'unknown',
                     u'Unbekannt.'),
                ),
            ),
            missing=unicode(''),
            oid='membership_type',
        )
        member_of_colsoc = colander.SchemaNode(
            colander.String(),
            title='Mitglied einer Verwertungsgesellschaft?',
            validator=colander.OneOf([x[0] for x in yes_no]),
            widget=deform.widget.RadioChoiceWidget(values=yes_no),
            missing=unicode(''),
            oid="other_colsoc",
        )
        name_of_colsoc = colander.SchemaNode(
            colander.String(),
            title=(u'Falls ja, welche? (Kommasepariert)'),
            missing=unicode(''),
            oid="colsoc_name",
        )

    class Shares(colander.Schema):
        """
        the number of shares a member wants to hold
        """
        num_shares = colander.SchemaNode(
            colander.Integer(),
            title='Anzahl Anteile (1-60)',
            default="1",
            validator=colander.Range(
                min=1,
                max=60,
                min_err=u'mindestens 1',
                max_err=u'höchstens 60',
            ),
            oid="num_shares")

    class MembershipForm(colander.Schema):
        """
        The Form consists of
        - Personal Data
        - Membership Information
        - Shares
        """
        person = PersonalDataCreateEdit(
            title=_(u"Personal Data"),
        )
        membership_info = MembershipInfo(
            title=_(u"Membership Requirements")
        )
        shares = Shares(
            title=_(u"Shares")
        )

    schema = MembershipForm()

    form = deform.Form(
        schema.bind(date=date),
        buttons=[
            deform.Button('submit', _(u'Submit')),
            deform.Button('reset', _(u'Reset'))
        ],
        use_ajax=True,
        renderer=ZPT_RENDERER,
    )

    # if the form has NOT been used and submitted, remove error messages if any
    if 'submit' not in request.POST:
        request.session.pop_flash()

    # if the form has been used and SUBMITTED, check contents
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)

        except ValidationFailure as exception:
            request.session.flash(
                _(u"Please note: There were errors, "
                  "please check the form below."),
                'danger',
                allow_duplicate=False)
            return{'form': exception.render()}

        def make_random_string():
            """
            used as email confirmation code
            """
            return u''.join(
                random.choice(
                    string.ascii_uppercase + string.digits
                ) for x in range(10))

        randomstring = make_random_string()
        while C3sMember.check_for_existing_confirm_code(randomstring):
            randomstring = make_random_string()

        # to store the data in the DB, an objet is created
        member = C3sMember(
            firstname=appstruct['person']['firstname'],
            lastname=appstruct['person']['lastname'],
            email=appstruct['person']['email'],
            password='UNSET',
            address1=appstruct['person']['address1'],
            address2=appstruct['person']['address2'],
            postcode=appstruct['person']['postcode'],
            city=appstruct['person']['city'],
            country=appstruct['person']['country'],
            locale=appstruct['person']['locale'],
            date_of_birth=appstruct['person']['date_of_birth'],
            email_is_confirmed=(
                True if appstruct['person']['email_is_confirmed'] == 'yes'
                else False),
            email_confirm_code=randomstring,
            date_of_submission=datetime.now(),
            membership_type=appstruct['membership_info']['membership_type'],
            member_of_colsoc=(
                appstruct['membership_info']['member_of_colsoc'] == u'yes'),
            name_of_colsoc=appstruct['membership_info']['name_of_colsoc'],
            num_shares=appstruct['shares']['num_shares'],
        )
        if 'legalentity' in appstruct['membership_info']['entity_type']:
            member.membership_type = u'investing'
            member.is_legalentity = True

        dbsession = DBSession()

        try:
            _temp = request.url.split('?')[1].split('=')
            if 'id' in _temp[0]:
                _id = _temp[1]

                # add a member with a DB id that had seen its entry deleted
                # before
                _mem = C3sMember.get_by_id(_id)
                if isinstance(_mem, NoneType):
                    member.id = _id
        except:
            pass

        # add member at next free DB id (default if member.id not set)
        try:
            dbsession.add(member)
            dbsession.flush()
            the_new_id = member.id
        except InvalidRequestError as exception:
            print("InvalidRequestError! %s") % exception
        except IntegrityError as exception:
            print("IntegrityError! %s") % exception

        # redirect to success page, then return the PDF
        # first, store appstruct in session
        request.session['appstruct'] = appstruct
        request.session[
            'appstruct']['locale'] = appstruct['person']['locale']

        # empty the messages queue (as validation worked anyways)
        request.session.pop_flash()
        return HTTPFound(  # redirect to success page
            location=request.route_url(
                'detail',
                member_id=the_new_id),
        )

    # if the form was submitted and gathered info shown on the success page,
    # BUT the user wants to correct their information:
    else:
        # remove annoying message from other session
        request.session.pop_flash()
        if 'appstruct' in request.session:
            appstruct = request.session['appstruct']
            # pre-fill the form with the values from last time
            form.set_appstruct(appstruct)

    html = form.render()

    return {'form': html}
