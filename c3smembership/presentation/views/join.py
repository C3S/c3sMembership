# -*- coding: utf-8 -*-
"""
This module holds the views for membership acquisition,
aka 'Application for Membership' (afm).

- join_c3s: the membership application form
- show_success: confirm data supplied
- success_check_email: send email with link
- success_verify_email: verify email address, present PDF link
- show_success_pdf: let user download her pdf for printout

Tests for these functions can be found in

- test_views_webdriver.py:JoinFormTests (webdriver: no coverage)
- test_views_webdriver.py:EmailVerificationTests (webdriver: no coverage)
- test_webtest.py (with coverage)

"""

from datetime import (
    date,
    datetime,
)
import logging
from types import NoneType

import colander
from colander import (
    Invalid,
    Range,
)
import deform
from deform import ValidationFailure
from pyramid.i18n import (
    get_locale_name,
)
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid_mailer.message import Message

from c3smembership.deform_text_input_slider_widget import (
    TextInputSliderWidget
)
from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.presentation.i18n import (
    _,
    ZPT_RENDERER,
)
from c3smembership.utils import (
    generate_pdf,
    send_accountant_mail,
)


LOG = logging.getLogger(__name__)


@view_config(
    renderer='c3smembership.presentation:templates/pages/join_form.pt',
    route_name='join')
def join_c3s(request):
    """
    This is the main membership application form view: Join C3S as member
    """
    # if another language was chosen by clicking on a flag
    # the add_locale_to_cookie subscriber has planted an attr on the request
    if hasattr(request, '_REDIRECT_'):

        _query = request._REDIRECT_
        # set language cookie
        request.response.set_cookie('locale', _query)
        request.locale = _query
        locale_name = _query
        return HTTPFound(location=request.route_url('join'),
                         headers=request.response.headers)
    else:
        locale_name = get_locale_name(request)

    from c3smembership.utils import country_codes
    # set default of Country select widget according to locale
    locale_country_mapping = {
        'de': 'DE',
        'en': 'GB',
    }
    country_default = locale_country_mapping.get(locale_name)

    class PersonalData(colander.MappingSchema):
        """
        colander schema for membership application form
        """
        firstname = colander.SchemaNode(
            colander.String(),
            title=_(u"(Real) First Name"),
            oid="firstname",
        )
        lastname = colander.SchemaNode(
            colander.String(),
            title=_(u"(Real) Last Name"),
            oid="lastname",
        )
        email = colander.SchemaNode(
            colander.String(),
            title=_(u'Email Address'),
            validator=colander.Email(),
            oid="email",
        )
        address1 = colander.SchemaNode(
            colander.String(),
            title=_(u'Address Line 1')
        )
        address2 = colander.SchemaNode(
            colander.String(),
            missing=unicode(''),
            title=_(u'Address Line 2')
        )
        postcode = colander.SchemaNode(
            colander.String(),
            title=_(u'Postal Code'),
            oid="postcode"
        )
        city = colander.SchemaNode(
            colander.String(),
            title=_(u'City'),
            oid="city",
        )
        country = colander.SchemaNode(
            colander.String(),
            title=_(u'Country'),
            default=country_default,
            widget=deform.widget.SelectWidget(
                values=country_codes),
            oid="country",
        )
        date_of_birth = colander.SchemaNode(
            colander.Date(),
            title=_(u'Date of Birth'),
            widget=deform.widget.DatePartsWidget(),
            default=date(2013, 1, 1),
            validator=Range(
                min=date(1913, 1, 1),
                # max 18th birthday, no minors through web formular
                max=date(
                    date.today().year-18,
                    date.today().month,
                    date.today().day),
                min_err=_(
                    u'Sorry, but we do not believe that the birthday you '
                    u'entered is correct.'),
                max_err=_(
                    u'Unfortunately, the membership application of an '
                    u'underaged person is currently not possible via our web '
                    u'form. Please send an email to office@c3s.cc.')
            ),
            oid="date_of_birth",
        )
        password = colander.SchemaNode(
            colander.String(),
            validator=colander.Length(min=5, max=100),
            widget=deform.widget.CheckedPasswordWidget(size=20),
            title=_(u'Password (to protect access to your data)'),
            description=_(u'We need a password to protect your data. After '
                          u'verifying your email you will have to enter it.'),
            oid='password',
        )
        locale = colander.SchemaNode(
            colander.String(),
            widget=deform.widget.HiddenWidget(),
            default=locale_name)

    class MembershipInfo(colander.Schema):
        """
        Basic member information.
        """
        yes_no = ((u'yes', _(u'Yes')),
                  (u'no', _(u'No')))
        membership_type = colander.SchemaNode(
            colander.String(),
            title=_(u'I want to become a ... '
                    u'(choose membership type, see C3S SCE statute sec. 4)'),
            description=_(u'choose the type of membership.'),
            widget=deform.widget.RadioChoiceWidget(
                values=(
                    (
                        u'normal',
                        _(u'FULL member. Full members have to be natural '
                          u'persons who register at least three works they '
                          u'created themselves with C3S. This applies to '
                          u'composers, lyricists and remixers. They get a '
                          u'vote.')),
                    (
                        u'investing',
                        _(u'INVESTING member. Investing members can be '
                          u'natural or legal entities or private companies '
                          u'that do not register works with C3S. They do '
                          u'not get a vote, but may counsel.'))
                ),
            ),
            oid='membership_type'
        )
        member_of_colsoc = colander.SchemaNode(
            colander.String(),
            title=_(
                u'Currently, I am a member of (at least) one other '
                u'collecting society.'),
            validator=colander.OneOf([x[0] for x in yes_no]),
            widget=deform.widget.RadioChoiceWidget(values=yes_no),
            oid="other_colsoc",
        )
        name_of_colsoc = colander.SchemaNode(
            colander.String(),
            title=_(u'If so, which one(s)? Please separate multiple '
                    u'collecting societies by comma.'),
            description=_(
                u'Please tell us which collecting societies '
                u'you are a member of. '
                u'If more than one, please separate them by comma.'),
            missing=unicode(''),
            oid="colsoc_name",
        )

    class Shares(colander.Schema):
        """
        the number of shares a member wants to hold

        this involves a slider widget: added to deforms widgets.
        see README.Slider.rst
        """
        num_shares = colander.SchemaNode(
            colander.Integer(),
            title=_(u"I want to buy the following number "
                    u"of Shares (50€ each, up to 3000€, see "
                    u"C3S statute sec. 5)"),
            description=_(
                u'You can choose any amount of shares between 1 and 60.'),
            default="1",
            widget=TextInputSliderWidget(
                size=3, css_class='num_shares_input'),
            validator=colander.Range(
                min=1,
                max=60,
                min_err=_(u'You need at least one share of 50 €.'),
                max_err=_(u'You may choose 60 shares at most (3000 €).'),
            ),
            oid="num_shares")

    class TermsInfo(colander.Schema):
        """
        some legal requirements
        """

        def empty_message_validator(node, value):
            """
            Validator for statute confirmation.
            """
            if not value:
                # raise without additional error message as the description
                # already explains the necessity of the checkbox
                raise Invalid(node, u'')

        got_statute = colander.SchemaNode(
            colander.Bool(true_val=u'yes'),
            title=_(
                u'I acknowledge that the statutes and membership dues '
                u'regulations determine periodic contributions '
                u'for full members.'),
            label=_(
                u'An electronic copy of the statute of the '
                u'C3S SCE has been made available to me (see link below).'),
            description=_(
                u'You must confirm to have access to the statute.'),
            widget=deform.widget.CheckboxWidget(),
            validator=empty_message_validator,
            required=True,
            oid='got_statute',
        )
        got_dues_regulations = colander.SchemaNode(
            colander.Bool(true_val=u'yes'),
            title=(u''),
            label=_(
                u'An electronic copy of the temporary membership dues '
                u'regulations of the C3S SCE has been made available to me '
                u'(see link below).'),
            description=_(
                u'You must confirm to have access to the temporary '
                u'membership dues regulations.'),
            widget=deform.widget.CheckboxWidget(),
            validator=empty_message_validator,
            required=True,
            oid='got_dues_regulations',
        )
        privacy_consent = colander.SchemaNode(
            colander.Bool(true_val=u'yes'),
            title=_(u'Privacy'),
            label=_(
                u'I hereby agree to my personal data entered in this form '
                u'being stored and processed for the purpose of membership '
                u'management. I have taken notice of the data privacy '
                u'statement. '
                u'https://www.c3s.cc/en/datenschutz/#dsgvo-membership (see '
                u'link below)'),
            widget=deform.widget.CheckboxWidget(),
            validator=empty_message_validator,
            required=True,
            oid='privacy_consent',
        )

    class MembershipForm(colander.Schema):
        """
        The Form consists of
        - Personal Data
        - Membership Information
        - Shares
        """
        person = PersonalData(
            title=_(u'Personal Data'),
        )
        membership_info = MembershipInfo(
            title=_(u'Membership Data')
        )
        shares = Shares(
            title=_(u'Shares')
        )
        acknowledge_terms = TermsInfo(
            title=_(u'Acknowledgement')
        )

    schema = MembershipForm()

    form = deform.Form(
        schema,
        buttons=[
            deform.Button('reset', _(u'Reset'), type='reset'),
            deform.Button('submit', _(u'Next'))
        ],
        use_ajax=True,
        renderer=ZPT_RENDERER
    )

    # if the form has NOT been used and submitted, remove error messages if any
    if 'submit' not in request.POST:
        request.session.pop_flash()

    # if the form has been used and SUBMITTED, check contents
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)

            # data sanity: if not in collecting society, don't save collsoc
            # name even if it was supplied through form
            if 'no' in appstruct['membership_info']['member_of_colsoc']:
                appstruct['membership_info']['name_of_colsoc'] = ''

        except ValidationFailure as validation_failure:
            request.session.flash(
                _(u'Please note: There were errors, '
                  u'please check the form below.'),
                'message_above_form',
                allow_duplicate=False)

            # If the validation error was not caused by the password field,
            # manually set an error to the password field because the user
            # needs to re-enter it after a validation error.
            form = validation_failure.field
            if form['person']['password'].error is None:
                form['person']['password'].error = Invalid(
                    None,
                    _(
                        u'Please re-enter your password. For security '
                        u'reasons your password is not cached and therefore '
                        u'needs to be re-entered in case of validation '
                        u'issues.'
                    ))
                validation_failure = ValidationFailure(form, None, form.error)

            return {'form': validation_failure.render()}

        appstruct['membership_info']['privacy_consent'] = datetime.now()
        request.session['appstruct'] = appstruct
        request.session['appstruct']['locale'] = \
            appstruct['person']['locale']
        # empty the messages queue (as validation worked anyways)
        deleted_msg = request.session.pop_flash()
        del deleted_msg
        return HTTPFound(
            location=request.route_url('success'),
        )

    # if the form was submitted and gathered info shown on the success page,
    # BUT the user wants to correct their information:
    else:
        # remove annoying message from other session
        deleted_msg = request.session.pop_flash()
        del deleted_msg
        if 'appstruct' in request.session:
            appstruct = request.session['appstruct']
            # pre-fill the form with the values from last time
            form.set_appstruct(appstruct)

    html = form.render()

    return {'form': html}


@view_config(
    renderer='c3smembership.presentation:templates/pages/join_check_data.pt',
    route_name='success')
def show_success(request):
    """
    This view shows a success page with the data gathered through the form
    and a link (button) back to the form
    in case some data is wrong/needs correction.
    There is also a button to confirm the dataset
    and have an email set to the user for validation.
    """
    # check if user has used the form or 'guessed' this URL
    if 'appstruct' in request.session:
        # we do have valid info from the form in the session
        appstruct = request.session['appstruct']
        # delete old messages from the session (from invalid form input)
        request.session.pop_flash('message_above_form')
        return {
            'firstname': appstruct['person']['firstname'],
            'lastname': appstruct['person']['lastname'],
        }
    return HTTPFound(location=request.route_url('join'))


def send_mail_confirmation_mail(
        member, base_url, email_sender_address, mailer, localizer,
        testing_mail_to_console):
    if 'de' in member.locale.lower():
        email_subject = u'C3S: E-Mail-Adresse bestätigen und Formular abrufen'
        email_body = u'''
Hallo {} {}!

bitte benutze diesen Link um deine E-Mail-Adresse zu bestätigen
und dein PDF herunterzuladen:

{}/verify/{}/{}

Danke!

Dein C3S Team
        '''
    else:
        email_subject = u'C3S: confirm your email address and load your PDF'
        email_body = u'''
Hello {} {}!

please use this link to verify your email address
and download your personalised PDF:

{}/verify/{}/{}

thanks!

Your C3S team
        '''
    message = Message(
        subject=email_subject,
        sender=email_sender_address,
        recipients=[member.email],
        body=email_body.format(
            member.firstname,
            member.lastname,
            base_url,
            member.email,
            member.email_confirm_code
        )
    )
    if 'true' in testing_mail_to_console:
        LOG.info(message.subject)
        LOG.info(message.recipients)
        LOG.info(message.body)
    else:
        mailer.send(message)


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'join_verification_email_sent.pt',
    route_name='success_check_email')
def success_check_email(request):
    """
    This view is called from the page that shows a user her data for correction
    by clicking a "send email" button.
    This view then sends out the email with a verification link
    and returns a note to go check mail.
    """
    # check if user has used the form (good) or 'guessed' this URL (bad)
    if 'appstruct' in request.session:

        appstruct = request.session['appstruct']

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

        email_confirm_code = make_random_string()
        while C3sMember.check_for_existing_confirm_code(email_confirm_code):
            email_confirm_code = make_random_string()  # pragma: no cover

        member = C3sMember(
            firstname=appstruct['person']['firstname'],
            lastname=appstruct['person']['lastname'],
            email=appstruct['person']['email'],
            password=appstruct['person']['password'],
            address1=appstruct['person']['address1'],
            address2=appstruct['person']['address2'],
            postcode=appstruct['person']['postcode'],
            city=appstruct['person']['city'],
            country=appstruct['person']['country'],
            locale=appstruct['person']['locale'],
            date_of_birth=appstruct['person']['date_of_birth'],
            email_is_confirmed=False,
            email_confirm_code=email_confirm_code,
            date_of_submission=datetime.now(),
            membership_type=appstruct['membership_info']['membership_type'],
            member_of_colsoc=(
                appstruct['membership_info']['member_of_colsoc'] == u'yes'),
            name_of_colsoc=appstruct['membership_info']['name_of_colsoc'],
            num_shares=appstruct['shares']['num_shares'],
            privacy_consent=appstruct['membership_info']['privacy_consent'],
        )
        DBSession().add(member)
        send_accountant_mail(request, member)

        send_mail_confirmation_mail(
            member,
            request.registry.settings['c3smembership.url'],
            request.registry.settings['c3smembership.notification_sender'],
            request.registry.get_mailer(request),
            request.localizer,
            request.registry.settings['testing.mail_to_console'])

        # make the session go away
        request.session.invalidate()
        return {
            'firstname': appstruct['person']['firstname'],
            'lastname': appstruct['person']['lastname'],
        }
    return HTTPFound(location=request.route_url('join'))


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'join_verify_email_address.pt',
    route_name='verify_email_password')
def success_verify_email(request):
    """
    This view is called via links sent in mails to verify mail addresses.
    It extracts both email and verification code from the URL.
    It will ask for a password
    and checks if there is a match in the database.

    If the password matches, and all is correct,
    the view shows a download link and further info.
    """
    user_email = request.matchdict['email']
    confirm_code = request.matchdict['code']
    # if we want to ask the user for her password (through a form)
    # we need to have a url to send the form to
    post_url = '/verify/' + user_email + '/' + confirm_code

    if 'submit' in request.POST:
        request.session.pop_flash('message_above_form')
        request.session.pop_flash('message_above_login')
        if 'password' in request.POST:
            _passwd = request.POST['password']

        # get matching dataset from DB
        member = C3sMember.get_by_code(confirm_code)

        if isinstance(member, NoneType):
            not_found_msg = _(
                u"Not found. Check verification URL. "
                "If all seems right, please use the form again.")
            return {
                'correct': False,
                'namepart': '',
                'result_msg': not_found_msg,
            }

        # check if the password is valid
        try:
            correct = C3sMember.check_password(member.id, _passwd)
        except AttributeError:
            correct = False
            request.session.flash(
                _(u'Wrong Password!'),
                'message_above_login')

        if (member.email == user_email) and correct:
            # set the email_is_confirmed flag in the DB for this signee
            member.email_is_confirmed = True
            namepart = member.firstname + member.lastname

            # Replace special characters with underscore
            import re
            pdf_file_name_part = re.sub(
                '[^a-zA-Z0-9]',
                '_',
                namepart)

            appstruct = {
                'firstname': member.firstname,
                'lastname': member.lastname,
                'email': member.email,
                'email_confirm_code': member.email_confirm_code,
                'address1': member.address1,
                'address2': member.address2,
                'postcode': member.postcode,
                'city': member.city,
                'country': member.country,
                'locale': member.locale,
                'date_of_birth': member.date_of_birth,
                'date_of_submission': member.date_of_submission,
                'membership_type': member.membership_type,
                'member_of_colsoc':
                    u'yes' if member.member_of_colsoc else u'no',
                'name_of_colsoc': member.name_of_colsoc,
                'num_shares': member.num_shares,
            }
            request.session['appstruct'] = appstruct

            # log this person in, using the session
            LOG.info('verified code and password for id %s', member.id)
            request.session.save()
            return {
                'firstname': member.firstname,
                'lastname': member.lastname,
                'code': member.email_confirm_code,
                'correct': True,
                'namepart': pdf_file_name_part,
                'result_msg': _("Success. Load your PDF!")
            }
    request.session.flash(
        _(u"Please enter your password."),
        'message_above_login',
        allow_duplicate=False
    )
    return {
        'post_url': post_url,
        'firstname': '',
        'lastname': '',
        'namepart': '',
        'correct': False,
        'result_msg': "something went wrong."
    }


@view_config(route_name='success_pdf')
def show_success_pdf(request):
    """
    Generates the membership application PDF to be signed by the applicant.
    """
    # check if user has used form or 'guessed' this URL
    if 'appstruct' in request.session:
        return generate_pdf(request.session['appstruct'])
    return HTTPFound(location=request.route_url('join'))
