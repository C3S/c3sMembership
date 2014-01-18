# -*- coding: utf-8 -*-

from c3smembership.utils import (
    generate_pdf,
    accountant_mail,
)
from c3smembership.models import (
    C3sMember,
    #C3sStaff,
    DBSession,
)
from types import NoneType
from pkg_resources import resource_filename
import colander
import deform
from deform import ValidationFailure
from colander import Invalid

from pyramid.i18n import (
    #TranslationStringFactory,
    get_localizer,
    get_locale_name,
)
from pyramid.view import view_config
from pyramid.threadlocal import get_current_request
from pyramid_mailer import get_mailer
from pyramid.httpexceptions import HTTPFound
#from pyramid.security import (
    #remember,
    #forget,
    #authenticated_userid,
#)
#from pyramid.url import route_url
from translationstring import TranslationStringFactory

deform_templates = resource_filename('deform', 'templates')
c3smembership_templates = resource_filename('c3smembership', 'templates')

my_search_path = (deform_templates, c3smembership_templates)

_ = TranslationStringFactory('c3smembership')


def translator(term):
    #print("=== this is def translator")
    return get_localizer(get_current_request()).translate(term)

my_template_dir = resource_filename('c3smembership', 'templates/')
deform_template_dir = resource_filename('deform', 'templates/')

zpt_renderer = deform.ZPTRendererFactory(
    [
        my_template_dir,
        deform_template_dir,
    ],
    translator=translator,
)
# the zpt_renderer above is referred to within the demo.ini file by dotted name

DEBUG = False
LOGGING = True

if LOGGING:  # pragma: no cover
    import logging
    log = logging.getLogger(__name__)


#@view_config(renderer='templates/disclaimer.pt',
#             route_name='disclaimer')
#def show_disclaimer(request):
#    """
#    This view simply shows a disclaimer, contained as text in a template.
#    """
#    if hasattr(request, '_REDIRECT_'):
#        return HTTPFound(location=route_url('disclaimer', request),
#                         headers=request.response.headers)
#    return {'foo': 'bar'}  # dummy values: template contains all text


#@view_config(renderer='templates/faq.pt',
#             route_name='faq')
#def show_faq(request):
#    """
#    This view simply shows an FAQ, contained as text in a template.
#    """
#    if hasattr(request, '_REDIRECT_'):  # pragma: no cover
#        return HTTPFound(location=request.route_url('faq'),
#                         headers=request.response.headers)
#    return {'foo': 'bar'}  # dummy values: template contains all text


#@view_config(renderer='templates/statute.pt',
#             route_name='statute')
#def show_statute(request):
#    """
#    This view simply shows the statute, contained as text in a template.
#    """
#    if hasattr(request, '_REDIRECT_'):  # pragma: no cover
#        return HTTPFound(location=request.route_url('statute'),
#                         headers=request.response.headers)
#    return {'foo': 'bar'}  # dummy values: template contains all text


#@view_config(renderer='templates/manifesto.pt',
#             route_name='manifesto')
#def show_manifesto(request):
#    """
#    This view simply shows the manifesto, contained as text in a template.
#    """
#    if hasattr(request, '_REDIRECT_'):  # pragma: no cover
#        return HTTPFound(location=request.route_url('manifesto'),
#                         headers=request.response.headers)
#    return {'foo': 'bar'}  # dummy values: template contains all text


@view_config(renderer='templates/success.pt',
             route_name='success')
def show_success(request):
    """
    This view shows a success page with the data gathered through the form
    and a link (button) back to the form
    in case some data is wrong/needs correction.
    There is also a button to confirm the dataset
    and have an email set to the user for validation.
    """
    #check if user has used the form or 'guessed' this URL
    if ('appstruct' in request.session):
        # we do have valid info from the form in the session
        appstruct = request.session['appstruct']
        # delete old messages from the session (from invalid form input)
        request.session.pop_flash('message_above_form')
        #print("show_success: locale: %s") % appstruct['_LOCALE_']
        return {
            'firstname': appstruct['person']['firstname'],
            'lastname': appstruct['person']['lastname'],
        }
    # 'else': send user to the form
    return HTTPFound(location=request.route_url('join'))


@view_config(route_name='success_pdf')
def show_success_pdf(request):
    """
    Given there is valid information in the session
    this view sends an encrypted mail to C3S staff with the users data set
    and returns a PDF for the user.

    It is called after visiting the verification URL/page/view in
    def success_verify_email below.
    """
    #check if user has used form or 'guessed' this URL
    if ('appstruct' in request.session):
        # we do have valid info from the form in the session
        #print("-- valid session with data found")
        # send mail to accountants // prepare a mailer
        mailer = get_mailer(request)
        # prepare mail
        appstruct = request.session['appstruct']
        message_recipient = request.registry.settings['c3smembership.mailaddr']
        appstruct['message_recipient'] = message_recipient
        the_mail = accountant_mail(appstruct)
        mailer.send(the_mail)

        return generate_pdf(request.session['appstruct'])
    # 'else': send user to the form
    #print("-- no valid session with data found")
    return HTTPFound(location=request.route_url('join'))


@view_config(
    renderer='templates/check-mail.pt',
    route_name='success_check_email')
def success_check_email(request):
    """
    This view is called from the page that shows a user her data for correction
    by clicking a "send email" button.
    This view then sends out the email with a verification link
    and returns a note to go check mail.
    """
    #check if user has used the form (good) or 'guessed' this URL (bad)

    if ('appstruct' in request.session):
        # we do have valid info from the form in the session (good)
        appstruct = request.session['appstruct']
        from pyramid_mailer.message import Message
        try:
            mailer = get_mailer(request)
        except:
            return HTTPFound(location=request.route_url('join'))
            # ToDo: handle excpetion

        # XXX TODO: check for locale, choose language for body text
        #import pdb; pdb.set_trace()
        # build the emails body
        body_lines = (  # a list of lines
            _(u"hello"), ' ', appstruct['person']['firstname'], ' ',
            appstruct['person']['lastname'], ''' !

''',
            _(u"please use this link to verify your email address "
              "and download your personalised PDF:"),
            u"""
 https://yes.c3s.cc/verify/""",
            appstruct['person']['email'], '/',
            appstruct['email_confirm_code'], '''

''',
            _(u"thanks!"), '''

''',
            _(u"your C3S team"),
        )
        the_mail_body = ''.join([line for line in body_lines])
        the_mail = Message(
            subject=_("C3S: confirm your email address and load your PDF"),
            sender="noreply@c3s.cc",
            recipients=[appstruct['person']['email']],
            body=the_mail_body
        )
        mailer.send(the_mail)
        #print(the_mail.body)

        # make the session go away
        request.session.invalidate()
        return {
            'firstname': appstruct['person']['firstname'],
            'lastname': appstruct['person']['lastname'],
        }
    # 'else': send user to the form
    return HTTPFound(location=request.route_url('join'))


# @view_config(
#     renderer='templates/verify_password.pt',
#     route_name='verify_password')
# def verify_password(request):
#     """
#     This view is called via links sent in mails to verify mail addresses.
#     It extracts both email and verification code from the URL
#     and checks if there is a match in the database.
#     """
#     #dbsession = DBSession()
#     # collect data from the URL/matchdict
#     user_email = request.matchdict['email']
#     #print(user_email)
#     confirm_code = request.matchdict['code']
#     #print(confirm_code)
#     # get matching dataset from DB
#     member = C3sMember.get_by_code(confirm_code)  # returns a member or None
#     #print(member)

#     return {'foo': 'bar'}


@view_config(
    renderer='templates/verify_password.pt',
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
    #dbsession = DBSession()
    #print('#'*80)
    # collect data from the URL/matchdict
    user_email = request.matchdict['email']
    #print(user_email)
    confirm_code = request.matchdict['code']
    #print(confirm_code)
    # if we want to ask the user for her password (through a form)
    # we need to have a url to send the form to
    post_url = '/verify/' + user_email + '/' + confirm_code

    if 'submit' in request.POST:
        #print("the form was submitted")
        request.session.pop_flash('message_above_form')
        request.session.pop_flash('message_above_login')
        # check for password ! ! !
        if 'password' in request.POST:
            _passwd = request.POST['password']
            #print("The password: %s" % _passwd)
        #else:
            # message: missing password!
        #    print('# message: missing password!')

        # get matching dataset from DB
        member = C3sMember.get_by_code(confirm_code)  # returns member or None

        if isinstance(member, NoneType):
            # member not found: FAIL!
            # print("a matching entry for this code was not found.")
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
        #print("member: %s" % member)
        #print("passwd correct? %s" % correct)
        # check if info from DB makes sense
        # -member

        if ((member.email == user_email) and correct):
            #print("-- found member, code matches, password too. COOL!")
            # set the email_is_confirmed flag in the DB for this signee
            member.email_is_confirmed = True
            #dbsession.flush()
            namepart = member.firstname + member.lastname
            import re
            PdfFileNamePart = re.sub(  # replace characters
                '[^a-zA-Z0-9]',  # other than these
                '_',  # with an underscore
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
                '_LOCALE_': member.locale,
                'date_of_birth': member.date_of_birth,
                'date_of_submission': member.date_of_submission,
                #'activity': set(activities),
                #'invest_member': u'yes' if member.invest_member else u'no',
                'membership_type': member.membership_type,
                'member_of_colsoc': u'yes' if member.member_of_colsoc else u'no',
                'name_of_colsoc': member.name_of_colsoc,
                #'opt_band': signee.opt_band,
                #'opt_URL': signee.opt_URL,
                'num_shares': member.num_shares,
            }
            request.session['appstruct'] = appstruct

            # log this person in, using the session
            log.info('verified code and password for id %s' % member.id)
            request.session.save()
            return {
                'firstname': member.firstname,
                'lastname': member.lastname,
                'code': member.email_confirm_code,
                'correct': True,
                'namepart': PdfFileNamePart,
                'result_msg': _("Success. Load your PDF!")
            }
    # else: code did not match OR SOMETHING...
    # just display the form
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


@view_config(renderer='templates/join.pt',
             route_name='join')
def join_c3s(request):
    """
    This is the main form view: Join C3S as member
    """
    import datetime
    from colander import Range

    #LOGGING = True

    #if LOGGING:  # pragma: no cover
        #import logging
        #log = logging.getLogger(__name__)
        #log.info("join...")

    # if another language was chosen by clicking on a flag
    # the add_locale_to_cookie subscriber has planted an attr on the request
    if hasattr(request, '_REDIRECT_'):
        #print("request._REDIRECT_: " + str(request._REDIRECT_))

        _query = request._REDIRECT_
        #print("_query: " + _query)
        # set language cookie
        request.response.set_cookie('_LOCALE_', _query)
        request._LOCALE_ = _query
        locale_name = _query
        #print("locale_name (from query_string): " + locale_name)
        #from pyramid.httpexceptions import HTTPFound
        #print("XXXXXXXXXXXXXXX ==> REDIRECTING ")
        return HTTPFound(location=request.route_url('join'),
                         headers=request.response.headers)
    # # if another language was chosen, pick it
    # if request._REDIRECT_ is not '':
    #     print("request.query_string: " + str(request.query_string))
    #     _query = request.query_string
    #     print("_query: " + _query)
    #     # set language cookie
    #     request.response.set_cookie('_LOCALE_', _query)
    #     request._LOCALE_ = _query
    #     locale_name = _query
    #     print("locale_name (from query_string): " + locale_name)
    #     from pyramid.httpexceptions import HTTPFound
    #     print("XXXXXXXXXXXXXXX ==> REDIRECTING ")
    #     return HTTPFound(location=request.route_url('intent'),
    #                      headers=request.response.headers)
    else:
        #locale_name = request._LOCALE_
        locale_name = get_locale_name(request)
        #print("locale_name (from request): " + locale_name)

    # check if user clicked on language symbol to have page translated
    # #print("request.query_string: " + str(request.query_string))
    # if 'l' in request.query_string:
    #     print("request.query_string: " + str(request.query_string))
    #     print("request.query_string[0]: " + str(request.query_string[0]))

    # from pyramid.httpexceptions import HTTPFound
    # if (request.query_string == '_LOCALE_=%s' % (locale_name)) or (
    #     request.query_string == 'l=%s' % (locale_name)):
    #     # set language cookie
    #     request.response.set_cookie('_LOCALE_', locale_name)
    #     return HTTPFound(location=request.route_url('intent'),
    #                      headers=request.response.headers)

    if DEBUG:  # pragma: no cover
        print "-- locale_name: " + str(locale_name)

    country_codes = [
        ('AT', _(u'Austria')),
        ('BE', _(u'Belgium')),
        ('BG', _(u'Bulgaria')),
        ('CH', _(u'Switzerland')),
        ('CZ', _(u'Czech Republic')),
        ('DE', _(u'Germany')),
        ('DK', _(u'Denmark')),
        ('ES', _(u'Spain')),
        ('EE', _(u'Estonia')),
        ('FI', _(u'Finland')),
        ('FR', _(u'France')),
        ('GB', _(u'United Kingdom')),
        ('GR', _(u'Greece')),
        ('HU', _(u'Hungary')),
        ('HR', _(u'Croatia')),
        ('IE', _(u'Ireland')),
        ('IS', _(u'Iceland')),
        ('IT', _(u'Italy')),
        ('LT', _(u'Lithuania')),
        ('LI', _(u'Liechtenstein')),
        ('LV', _(u'Latvia')),
        ('LU', _(u'Luxembourg')),
        ('MT', _(u'Malta')),
        ('NL', _(u'Netherlands')),
        ('NO', _(u'Norway')),
        ('PL', _(u'Poland')),
        ('PT', _(u'Portugal')),
        ('SK', _(u'Slovakia')),
        ('SI', _(u'Slovenia')),
        ('SE', _(u'Sweden')),
        ('XX', _(u'other'))
    ]
    # set default of Country select widget according to locale
    LOCALE_COUNTRY_MAPPING = {
        'de': 'DE',
        #'da': 'DK',
        'en': 'GB',
        #'es': 'ES',
        #'fr': 'FR',
    }
    country_default = LOCALE_COUNTRY_MAPPING.get(locale_name)
    if DEBUG:  # pragma: no cover
        print("== locale is :" + str(locale_name))
        print("== choosing :" + str(country_default))

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
            title=_(u'Email'),
            validator=colander.Email(),
            oid="email",
        )
        password = colander.SchemaNode(
            colander.String(),
            validator=colander.Length(min=5, max=100),
            widget=deform.widget.PasswordWidget(size=20),
            title=_(u"Password (to protect access to your data)"),
            description=_("We need a password to protect your data. After "
                          "verifying your email you will have to enter it."),
            oid="password",
        )

        address1 = colander.SchemaNode(
            colander.String(),
            title=_(u'Address Line 1')
        )
        address2 = colander.SchemaNode(
            colander.String(),
            missing=unicode(''),
            title=_(u"Address Line 2")
        )
        postcode = colander.SchemaNode(
            colander.String(),
            title=_(u'Post Code'),
            oid="postcode"
        )
        city = colander.SchemaNode(
            colander.String(),
            title=_(u'City'),
            oid="city",
        )
      #  region = colander.SchemaNode(
      #      colander.String(),
      #      title=_(u'Federal State / Province / County'),
      #      missing=unicode(''))
        country = colander.SchemaNode(
            colander.String(),
            title=_(u'Country'),
            default=country_default,
            widget=deform.widget.SelectWidget(
                values=country_codes),
            oid="country",
        )

       # TODO:
       # Date of birth (dd/mm/yyyy) (three fields)
       # size doesn't have any effect?!
        date_of_birth = colander.SchemaNode(
            colander.Date(),
            title=_(u'Date of Birth'),
            #css_class="hasDatePicker",
            widget=deform.widget.DatePartsWidget(),
            default=datetime.date(2013, 1, 1),
            validator=Range(
                min=datetime.date(1913, 1, 1),
                max=datetime.date(2000, 1, 1),
                min_err=_(u'${val} is earlier than earliest date ${min}'),
                max_err=_(u'${val} is later than latest date ${max}')
            ),
            oid="date_of_birth",
        )

        # type_of_creator = (('composer', _(u'composer')),
        #                    ('lyricist', _(u'lyricist')),
        #                    ('music producer', _(u'music producer')),
        #                    ('remixer', _(u'remixer')),
        #                    ('dj', _(u'DJ')))

        # activity = colander.SchemaNode(
        #     deform.Set(allow_empty=True),
        #     title=_(
        #         u"I'm musically involved in creating at least three songs, "
        #         "and I\'m considering to ask C3S to administer the rights "
        #         " to some of my songs. I am active as a "
        #         "(multiple selection possible)"),
        #     widget=deform.widget.CheckboxChoiceWidget(
        #         values=type_of_creator),
        #     missing=unicode(''),
        #     oid="activity",)
        _LOCALE_ = colander.SchemaNode(colander.String(),
                                       widget=deform.widget.HiddenWidget(),
                                       default=locale_name)

    class MembershipInfo(colander.Schema):

        yes_no = ((u'yes', _(u'Yes')),
                  (u'no', _(u'No')))

     #   at_least_three_works = colander.SchemaNode(
     #       colander.String(),
     #       title=_(u'I have been the (co-)creator of at least three titles '
     #               'in one of the functions mentioned under (1)'),
     #       validator=colander.OneOf([x[0] for x in yes_no]),
     #       widget=deform.widget.RadioChoiceWidget(values=yes_no))

        ## TODO: inColSocName if member_of_colsoc = yes
        ## css/jquery: fixed; TODO: validator
        #def colsoc_validator(node, form):
            #log.info("validating...........................................")
            #print(value['member_of_colsoc'])
            #log.info(node.get('other_colsoc'))
            #log.info(node.get('other_colsoc-1'))
            #log.info(node.cstruct_children('other_colsoc'))
            #log.info(node.get_value('other_colsoc-1'))
            #log.info(dir(node))
            #log.info(node['member_of_colsoc'])
            #import pdb; pdb.set_trace()
            #if value['member_of_colsoc']
            #exc = colander.Invalid(
            #    form, "if colsoc, give name!")
            #exc['name_of_colsoc'] = "if colsoc, give name!"
            #log.info("end----------------------------------------")
            #pass

        membership_type = colander.SchemaNode(
            colander.String(),
            title=_(u'I want to become a ... (choose membership type, see C3S SCE statute sec. 4)'),
            description=_(u'choose the type of membership.'),
            widget=deform.widget.RadioChoiceWidget(
                values=(
                    (u'normal',
                     _(u'FULL member. Full members have to be natural persons who register at least three works with C3S they created themselves. This applies to composers, lyricists and remixers. They get a vote.')),
                    (u'investing',
                     _(u'INVESTING member. Investing members can be natural or legal entities or private companies that do not register works with C3S. They do not get a vote, but may counsel.'))
                ),
            )
        )

        # member_is_artist = colander.SchemaNode(
        #     colander.String(),
        #     title=_(
        #         u'I am at least one of: composer, lyricist, '
        #         'remixer, arranger, producer, DJ (i.e. musician)'),
        #     description=_(
        #         u'You have to be a musician to become a regular member of C3S SCE.'
        #         'Or choose to become a supporting member.'),
        #     validator=colander.OneOf([x[0] for x in yes_no]),
        #     widget=deform.widget.RadioChoiceWidget(
        #         values=(yes_no),
        #     ),
        # )
        member_of_colsoc = colander.SchemaNode(
            colander.String(),
            title=_(
                u'Currently, I am a member of (at least) one other collecting society.'),
            validator=colander.OneOf([x[0] for x in yes_no]),
            widget=deform.widget.RadioChoiceWidget(values=yes_no),
            oid="other_colsoc",
            #validator=colsoc_validator
        )
        name_of_colsoc = colander.SchemaNode(
            colander.String(),
            title=_(u'If so, which one(s)? (comma separated)'),
            description=_(
                u'Please tell us which collecting societies '
                'you are a member of. '
                'If more than one, please separate them by comma(s).'),
            missing=unicode(''),
            oid="colsoc_name",
            #validator=colander.All(
            #    colsoc_validator,
            #)
        )

        def statute_validator(node, value):
            if not value:
                raise Invalid(
                    node,
                    _(u'You must confirm to have access '
                      u'to the C3S SCE statute'))

        got_statute = colander.SchemaNode(
            #colander.String(),
            colander.Bool(true_val=u'yes'),
            title=_(
                u'An electronic copy of the statute of the '
                u'C3S SCE has been made available to me. (see link below)'),
            description=_(
                u'You must confirm to have access to the statute.'),
            #widget=deform.widget.CheckboxChoiceWidget(
            #    values=(('yes', _(u'Yes')),)),
            widget=deform.widget.CheckboxWidget(),
            #validator=colander.OneOf(['yes', ]),
            validator=statute_validator,
            required=True,
            label=_('Yes'),
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
                    u"of Shares (50€ each, up to 3000€, see C3S statute sec. 5)"),
            description=_(
                u'You can choose any amount of shares between 1 and 60.'),
            default="1",
            widget=deform.widget.TextInputSliderWidget(
                size=3, css_class='num_shares_input'),
            validator=colander.Range(
                min=1,
                max=60,
                min_err=_(u"You need at least one share of 50 Euro."),
                max_err=_(u"You may choose 60 shares at most. (3000 Euro)"),
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
            #description=_(u"this is a test"),
            #css_class="thisisjustatest"
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
        renderer=zpt_renderer
    )

    # if the form has NOT been used and submitted, remove error messages if any
    if not 'submit' in request.POST:
        request.session.pop_flash()

    # if the form has been used and SUBMITTED, check contents
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            #print("the appstruct from the form: %s \n") % appstruct
            #for thing in appstruct:
            #    print("the thing: %s") % thing
            #    print("type: %s") % type(thing)

            # data sanity: if not in collecting society, don't save
            #  collsoc name even if it was supplied through form
            if 'no' in appstruct['membership_info']['member_of_colsoc']:
                appstruct['membership_info']['name_of_colsoc'] = ''
                print appstruct['membership_info']['name_of_colsoc']
                #print '-'*80

        except ValidationFailure, e:
            #print("the appstruct from the form: %s \n") % appstruct
            #for thing in appstruct:
            #    print("the thing: %s") % thing
            #    print("type: %s") % type(thing)
            print(e)
            #message.append(
            request.session.flash(
                _(u"Please note: There were errors, "
                  "please check the form below."),
                'message_above_form',
                allow_duplicate=False)
            return{'form': e.render()}

        def make_random_string():
            """
            used as email confirmation code
            """
            import random
            import string
            return ''.join(
                random.choice(
                    string.ascii_uppercase + string.digits
                ) for x in range(10))

        # make confirmation code and
        randomstring = make_random_string()
        # check if confirmation code is already used
        while (C3sMember.check_for_existing_confirm_code(randomstring)):
            # create a new one, if the new one already exists in the database
            randomstring = make_random_string()  # pragma: no cover

        from datetime import datetime
        from sqlalchemy.exc import (
            InvalidRequestError,
            IntegrityError
        )
        # to store the data in the DB, an objet is created
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
            locale=appstruct['person']['_LOCALE_'],
            date_of_birth=appstruct['person']['date_of_birth'],
            email_is_confirmed=False,
            email_confirm_code=randomstring,
            #is_composer=('composer' in appstruct['activity']),
            #is_lyricist=('lyricist' in appstruct['activity']),
            #is_producer=('music producer' in appstruct['activity']),
            #is_remixer=('remixer' in appstruct['activity']),
            #is_dj=('dj' in appstruct['activity']),
            date_of_submission=datetime.now(),
            #invest_member=(
            #    appstruct['membership_info']['invest_member'] == u'yes'),
            membership_type=appstruct['membership_info']['membership_type'],
            member_of_colsoc=(
                appstruct['membership_info']['member_of_colsoc'] == u'yes'),
            name_of_colsoc=appstruct['membership_info']['name_of_colsoc'],
            #opt_band=appstruct['opt_band'],
            #opt_URL=appstruct['opt_URL'],
            num_shares=appstruct['shares']['num_shares'],
        )
        dbsession = DBSession()
        try:
            dbsession.add(member)
            appstruct['email_confirm_code'] = randomstring
        except InvalidRequestError, e:  # pragma: no cover
            print("InvalidRequestError! %s") % e
        except IntegrityError, ie:  # pragma: no cover
            print("IntegrityError! %s") % ie

        # send mail to accountants // prepare a mailer
        #mailer = get_mailer(request)
        # prepare mail
        #the_mail = accountant_mail(appstruct)
        #mailer.send(the_mail)
        #log.info("NOT sending mail...")

        #return generate_pdf(appstruct)  # would just return a PDF

        # redirect to success page, then return the PDF
        # first, store appstruct in session
        request.session['appstruct'] = appstruct
        request.session['appstruct']['_LOCALE_'] = appstruct['person']['_LOCALE_']
        #from pyramid.httpexceptions import HTTPFound
        #
        # empty the messages queue (as validation worked anyways)
        deleted_msg = request.session.pop_flash()
        del deleted_msg
        return HTTPFound(  # redirect to success page
            location=request.route_url('success'),
        )

    # if the form was submitted and gathered info shown on the success page,
    # BUT the user wants to correct their information:
    else:
        # remove annoying message from other session
        deleted_msg = request.session.pop_flash()
        del deleted_msg
        if ('appstruct' in request.session):
            #print("form was not submitted, but found appstruct in session.")
            appstruct = request.session['appstruct']
            #print("the appstruct: %s") % appstruct
            # pre-fill the form with the values from last time
            form.set_appstruct(appstruct)
            #import pdb
            #pdb.set_trace()
            #form = deform.Form(schema,
            #           buttons=[deform.Button('submit', _(u'Submit'))],
            #           use_ajax=True,
            #           renderer=zpt_renderer
            #           )

    html = form.render()

    return {'form': html}
