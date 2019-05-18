# -*- coding: utf-8 -*-
"""
This module has functionality for staff to enter new member application
datasets into the database from the backend.
"""
from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.presentation.i18n import (
    _,
    ZPT_RENDERER,
)
from c3smembership.utils import (
    country_codes,
)

import colander
from colander import (
    # Invalid,
    Range,
)
from datetime import (
    date,
    datetime,
)
import deform
from deform import ValidationFailure

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from sqlalchemy.exc import (
    InvalidRequestError,
    IntegrityError
)
from types import NoneType

country_default = 'Germany'


@view_config(
    route_name='new_member',
    permission='manage',
    renderer='c3smembership.presentation:templates/pages/'
             'membership_member_new.pt')
def new_member(request):
    '''
    let staff create a new member entry, when receiving input via dead wood
    '''

    # XXX check if submitted, etc...

    class PersonalData(colander.MappingSchema):
        """
        colander schema for membership application form
        """
        firstname = colander.SchemaNode(
            colander.String(),
            title=u'Vorname (b. Körpersch.: Ansprechpartner)',
            oid="firstname",
        )
        lastname = colander.SchemaNode(
            colander.String(),
            title=u'Nachname (b. Körpersch.: Name der Körperschaft)',
            oid="lastname",
        )
        email = colander.SchemaNode(
            colander.String(),
            title=_(u'E-Mail'),
            validator=colander.Email(),
            oid="email",
        )
        passwort = colander.SchemaNode(
            colander.String(),
            widget=deform.widget.HiddenWidget(),
            default='NoneSet',
            missing='NoneSetPurposefully'
        )
        address1 = colander.SchemaNode(
            colander.String(),
            title='Adresse Zeile 1'
        )
        address2 = colander.SchemaNode(
            colander.String(),
            missing=unicode(''),
            title='Adresse Zeile 2'
        )
        postcode = colander.SchemaNode(
            colander.String(),
            title='Postleitzahl',
            oid="postcode"
        )
        city = colander.SchemaNode(
            colander.String(),
            title='Ort',
            oid="city",
        )
        country = colander.SchemaNode(
            colander.String(),
            title='Land',
            default=country_default,
            widget=deform.widget.SelectWidget(
                values=country_codes),
            oid="country",
        )
        date_of_birth = colander.SchemaNode(
            colander.Date(),
            title='Geburtsdatum',
            # widget=deform.widget.DatePartsWidget(
            #    inline=True),
            default=date(1970, 1, 1),
            oid="date_of_birth",
        )
        locale = colander.SchemaNode(
            colander.String(),
            widget=deform.widget.HiddenWidget(),
            default='de',
            missing='de',
        )

    class MembershipInfo(colander.Schema):

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
            # validator=colsoc_validator
        )
        name_of_colsoc = colander.SchemaNode(
            colander.String(),
            title=(u'Falls ja, welche? (Kommasepariert)'),
            missing=unicode(''),
            oid="colsoc_name",
            # validator=colander.All(
            #    colsoc_validator,
            # )
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
        person = PersonalData(
            title=_(u"Personal Data"),
            # description=_(u"this is a test"),
            # css_class="thisisjustatest"
        )
        membership_info = MembershipInfo(
            title=_(u"Membership Requirements")
        )
        shares = Shares(
            title=_(u"Shares")
        )

    schema = MembershipForm()

    form = deform.Form(
        schema,
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
        # print('ping!')

    # if the form has been used and SUBMITTED, check contents
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            # print("the appstruct from the form: %s \n") % appstruct
            # for thing in appstruct:
            #    print("the thing: %s") % thing
            #    print("type: %s") % type(thing)

            # data sanity: if not in collecting society, don't save
            #  collsoc name even if it was supplied through form
            # if 'no' in appstruct['membership_info']['member_of_colsoc']:
            #    appstruct['membership_info']['name_of_colsoc'] = ''
            #    print appstruct['membership_info']['name_of_colsoc']
            # print '-'*80

        except ValidationFailure as e:
            # print("Validation Failure!")
            # print("the request.POST: %s \n" % request.POST)
            # for thing in request.POST:
            #    print("the thing: %s") % thing
            #    print("type: %s") % type(thing)
            # print(e.args)
            # print(e.error)
            # print(e.message)
            request.session.flash(
                _(u"Please note: There were errors, "
                  "please check the form below."),
                'danger',
                allow_duplicate=False)
            return{'form': e.render()}

        def make_random_string():
            """
            used as email confirmation code
            """
            import random
            import string
            return u''.join(
                random.choice(
                    string.ascii_uppercase + string.digits
                ) for x in range(10))

        # make confirmation code and
        randomstring = make_random_string()
        # check if confirmation code is already used
        while (C3sMember.check_for_existing_confirm_code(randomstring)):
            # create a new one, if the new one already exists in the database
            randomstring = make_random_string()  # pragma: no cover

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
            email_is_confirmed=False,
            email_confirm_code=randomstring,
            # is_composer=('composer' in appstruct['activity']),
            # is_lyricist=('lyricist' in appstruct['activity']),
            # is_producer=('music producer' in appstruct['activity']),
            # is_remixer=('remixer' in appstruct['activity']),
            # is_dj=('dj' in appstruct['activity']),
            date_of_submission=datetime.now(),
            # invest_member=(
            #    appstruct['membership_info']['invest_member'] == u'yes'),
            membership_type=appstruct['membership_info']['membership_type'],
            member_of_colsoc=(
                appstruct['membership_info']['member_of_colsoc'] == u'yes'),
            name_of_colsoc=appstruct['membership_info']['name_of_colsoc'],
            # opt_band=appstruct['opt_band'],
            # opt_URL=appstruct['opt_URL'],
            num_shares=appstruct['shares']['num_shares'],
        )
        if 'legalentity' in appstruct['membership_info']['entity_type']:
            # print "this is a legal entity"
            member.membership_type = u'investing'
            member.is_legalentity = True

        dbsession = DBSession()

        try:
            _temp = request.url.split('?')[1].split('=')
            if 'id' in _temp[0]:
                _id = _temp[1]
                # print("the id we want to recreate: %s" % _id)

            # add a member with a DB id that had seen its entry deleted before
                _mem = C3sMember.get_by_id(_id)  # load from id
                if isinstance(_mem, NoneType):  # check deletion status
                    member.id = _id  # set id as specified
        except:
            # print "no splitable url params found, creating new entry"
            pass

        # add member at next free DB id (default if member.id not set)
        try:
            dbsession.add(member)
            dbsession.flush()
            # print(member.id)
            the_new_id = member.id
            # appstruct['email_confirm_code'] = randomstring  # ???
        except InvalidRequestError, e:  # pragma: no cover
            print("InvalidRequestError! %s") % e
        except IntegrityError, ie:  # pragma: no cover
            print("IntegrityError! %s") % ie

        # send mail to accountants // prepare a mailer
        # mailer = get_mailer(request)
        # prepare mail
        # the_mail = accountant_mail(appstruct)
        # mailer.send(the_mail)
        # log.info("NOT sending mail...")

        # return generate_pdf(appstruct)  # would just return a PDF

        # redirect to success page, then return the PDF
        # first, store appstruct in session
        request.session['appstruct'] = appstruct
        request.session[
            'appstruct']['locale'] = appstruct['person']['locale']
        # from pyramid.httpexceptions import HTTPFound
        #
        # empty the messages queue (as validation worked anyways)
        deleted_msg = request.session.pop_flash()
        del deleted_msg
        return HTTPFound(  # redirect to success page
            location=request.route_url(
                'detail',
                member_id=the_new_id),
        )

    # if the form was submitted and gathered info shown on the success page,
    # BUT the user wants to correct their information:
    else:
        # remove annoying message from other session
        deleted_msg = request.session.pop_flash()
        del deleted_msg
        if ('appstruct' in request.session):
            # print("form was not submitted, but found appstruct in session.")
            appstruct = request.session['appstruct']
            # print("the appstruct: %s") % appstruct
            # pre-fill the form with the values from last time
            form.set_appstruct(appstruct)
            # import pdb
            # pdb.set_trace()
            # form = deform.Form(schema,
            #           buttons=[deform.Button('submit', _(u'Submit'))],
            #           use_ajax=True,
            #           renderer=zpt_renderer
            #           )

    html = form.render()

    return {'form': html}
