# -*- coding: utf-8 -*-
from c3smembership.models import (
    C3sMember,
    C3sStaff,
    DBSession,
    Group,
    #Shares,
    #Membership,
    #MembershipNumber,
)
from c3smembership.gnupg_encrypt import encrypt_with_gnupg
import colander
from colander import Range
from datetime import (
    datetime,
    date
)
import deform
from deform import ValidationFailure
import math
from pkg_resources import resource_filename
from pyramid.i18n import (
    get_localizer,
)
#from pyramid.request import Request
#from pyramid.response import Response
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from pyramid.view import view_config
from pyramid.threadlocal import get_current_request
from pyramid.httpexceptions import HTTPFound
#from pyramid.security import (
#    authenticated_userid,
    #forget,
    #remember,
#)
#from pyramid.url import route_url

#from pyramid_mailer import get_mailer
#from pyramid_mailer.message import Message
from sqlalchemy.exc import (
    IntegrityError,
    #ResourceClosedError,
)
import tempfile
from translationstring import TranslationStringFactory
from types import NoneType
#import unicodecsv

deform_templates = resource_filename('deform', 'templates')
c3smembership_templates = resource_filename(
    'c3smembership', 'templates')

my_search_path = (deform_templates, c3smembership_templates)

_ = TranslationStringFactory('c3smembership')


def translator(term):
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


@view_config(renderer='templates/stats.pt',
             permission='manage',
             route_name='stats')
def stats_view(request):
    """
    This view lets accountants view statistics:
    how many membership applications, real members, shares, etc.
    """
    return {
        # form submissions
        '_number_of_datasets': C3sMember.get_number(),
        'afm_shares_unpaid': C3sMember.afm_num_shares_unpaid(),
        'afm_shares_paid': C3sMember.afm_num_shares_paid(),
        # shares
        #'num_shares': Shares.get_total_shares(),
        # memberships
        #'num_memberships': Membership.get_number(),
        #'num_ms_nat': Membership.get_number(),  # XXX check!
        #'num_ms_jur': '0',  # XXX Membership.num_ms_jur(),
        #'num_ms_norm': Membership.num_ms_norm(),
        #'num_ms_inves': Membership.num_ms_invest(),
        # staff figures
        'num_staff': len(C3sStaff.get_all())
    }


@view_config(renderer='templates/toolbox.pt',
             permission='manage',
             route_name='toolbox')
def toolbox(request):
    """
    This view shows some options
    """
    return {'foo': 'bar'}


@view_config(renderer='templates/staff.pt',
             permission='manage',
             route_name='staff')
def staff_view(request):
    """
    This view lets admins edit staff/cashier personnel:
    who may act as cashier etc.?
    """
    _staffers = C3sStaff.get_all()

    class Staffer(colander.MappingSchema):
        login = colander.SchemaNode(
            colander.String(),
            title='login',
        )
        password = colander.SchemaNode(
            colander.String(),
            title='passwort',
        )

    schema = Staffer()

    stafferform = deform.Form(
        schema,
        buttons=[
            deform.Button('new_staffer', 'save')
        ]
    )

    if 'action' in request.POST:
        #print(request.POST['id'])
        try:
            _staffer = C3sStaff.get_by_id(int(request.POST['id']))
        except:
        #    print("exception!")
            return HTTPFound(location=request.route_url('staff'))
        #print(request.POST['action'])
        if request.POST['action'] == u'delete':
            #print("will delete staff id %s" % _staffer.id)
            C3sStaff.delete_by_id(_staffer.id)
            #print("deleted staff id %s" % _staffer.id)
            # send mail
            encrypted = encrypt_with_gnupg('''hi,
%s was deleted from the backend by %s.

best,
your membership tool''' % (_staffer.login,
                           request.authenticated_userid))
            message = Message(
                subject='[C3S Yes] staff was deleted.',
                sender='noreply@c3s.cc',
                recipients=[
                    request.registry.settings['c3smembership.mailaddr']],
                body=encrypted
            )
            mailer = get_mailer(request)
            mailer.send(message)
            return HTTPFound(location=request.route_url('staff'))
        elif request.POST['action'] == 'edit':
            appstruct = {
                'login': _staffer.login,
                'password': '_UNCHANGED_',
            }
            stafferform.set_appstruct(appstruct)

    if 'new_staffer' in request.POST:
        #print "new staffer!"
        controls = request.POST.items()
        try:
            appstruct = stafferform.validate(controls)
            #print('validated!')
        except ValidationFailure, e:
            return {
                'stafferform': e.render()
            }
        # XXX login must be unique!
        existing = C3sStaff.get_by_login(appstruct['login'])
        if existing is not None:
            #print "that staffer exists!"
            if u'_UNCHANGED_' in appstruct['password']:
                pass
            else:
                existing.password = appstruct['password']
                existing.last_password_change = datetime.now()
            encrypted = encrypt_with_gnupg('''hi,
the password of %s was changed by %s.

best,
your membership tool''' % (existing.login,
                           request.authenticated_userid))
            message = Message(
                subject='[C3S Yes] staff password changed.',
                sender='noreply@c3s.cc',
                recipients=[
                    request.registry.settings['c3smembership.mailaddr']],
                body=encrypted
            )

        else:  # create new entry
            staffer = C3sStaff(
                login=appstruct['login'],
                password=appstruct['password'],
                email=u'',
            )
            staffer.groups = [Group.get_staffers_group()]
            #print "about to add user"
            DBSession.add(staffer)
            DBSession.flush()
            print "added staffer"
            # send mail
            encrypted = encrypt_with_gnupg('''hi,
%s was added to the backend by %s.

best,
your membership tool''' % (staffer.login,
                           request.authenticated_userid))
            message = Message(
                subject='[C3S Yes] staff was added.',
                sender='noreply@c3s.cc',
                recipients=[
                    request.registry.settings['c3smembership.mailaddr']],
                body=encrypted
            )
            mailer = get_mailer(request)
            mailer.send(message)

        return HTTPFound(
            request.route_url('staff')
        )

    return {
        'staffers': _staffers,
        'stafferform': stafferform.render(),
    }


@view_config(renderer='templates/delete_afms.pt',
             permission='manage',
             route_name='delete_afms')
def delete_afms(request):
    '''
    delete a bunch of AfMs in one go
    '''
    class DeleteAfMRange(colander.MappingSchema):
        first = colander.SchemaNode(
            colander.Integer(),
            title='first ID to delete'
        )
        last = colander.SchemaNode(
            colander.Integer(),
            title='last ID to delete'
        )
    schema = DeleteAfMRange()
    delete_range_form = deform.Form(
        schema,
        buttons=[deform.Button('delete_them', 'DELETE')]
    )
    if 'first' in request.POST:
        print "form was submitted!"
        print "first ID to delete: %s" % request.POST['first']
        controls = request.POST.items()
        try:
            appstruct = delete_range_form.validate(controls)
            #print('validated!')
            #print appstruct
            _first = appstruct['first']
            _last = appstruct['last']
            assert(_first < _last)
        except ValidationFailure, e:
            return {
                'resetform': e.render()
            }
        # delete entries here :-)
        for i in range(_first, _last+1):
            #print i
            try:
                #_del = C3sMember.delete_by_id(i)
                C3sMember.delete_by_id(i)
                #print 'deleted %s' % _del
            except:
                print 'id %s didnt exist'
        return HTTPFound(request.route_url('dashboard_only'))
    return {
        'delete_form': delete_range_form.render()
    }


@view_config(permission='manage',
             route_name='mail_mail_confirmation')
def mail_mail_conf(request):
    '''
    send email to member to confirm her email address by clicking a link
    '''
    afmid = request.matchdict['memberid']
    afm = C3sMember.get_by_id(afmid)
    if isinstance(afm, NoneType):
        request.session.flash(
            'id not found. no mail sent.',
            'messages')
        return HTTPFound(request.route_url('dashboard',
                                           number=request.cookies['on_page'],
                                           order=request.cookies['order'],
                                           orderby=request.cookies['orderby']))

    import random
    import string
    _looong_token = u''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in range(13))
    _url = (request.registry.settings['c3smembership.url'] +
            '/vae/' + afm.email_confirm_code +
            '/' + _looong_token + '/' + afm.email)

    _body = u'''[english version below]

Liebe_r C3S-Unterstützer_in,

Uns wurde am {1} diese Mail-Adresse genannt, um mit Dir in Kontakt treten
zu können.

Um sicherzustellen, dass sich nicht versehentlich ein Tippfehler o.ä.
eingeschlichen hat, bitten wir Dich um eine Bestätigung der Adresse. Dafür
brauchst Du nur den folgenden Link aufzurufen:

  {0}

Solltest Du diese Adresse nicht bei uns angegeben haben, antworte bitte kurz
auf diese E-Mail.


Viele Grüße :: Das C3S-Team

++++++++++++++++++++++++++++++++++++++++++++++++++

Dear C3S-Supporter,

We were given this Email address to contact you on {2}. To make sure this
address really works, we are asking you to confirm your address.
Please click on the following link:

    {0}

If you did not give this email address to C3S, please reply briefly to this
email.

Best :: The C3S Team
'''.format(
    _url,
    afm.date_of_submission.strftime("%d.%m.%Y"),
    afm.date_of_submission.strftime("%d %b %Y"),
)

    log.info("mailing mail confirmation to AFM # %s" % afm.id)

    message = Message(
        subject=(u'[C3S] Please confirm your Email address! '
                 u'/ Bitte E-Mail-Adresse bestätigen!'),
        sender='yes@c3s.cc',
        recipients=[afm.email],
        body=_body
    )
    #print(message.subject)
    #print(message.body)
    mailer = get_mailer(request)
    mailer.send(message)
    afm.email_confirm_token = _looong_token
    afm.email_confirm_mail_date = datetime.now()
    return HTTPFound(request.route_url('dashboard',
                                       number=request.cookies['on_page'],
                                       order=request.cookies['order'],
                                       orderby=request.cookies['orderby']) +
                     '#member_' + str(afm.id))


@view_config(renderer='templates/verify-mail.pt',
             route_name='verify_afm_email')
def verify_mailaddress_conf(request):
    '''
    let member confirm her email address by clicking a link
    '''
    user_email = request.matchdict['email']
    refcode = request.matchdict['refcode']
    token = request.matchdict['token']
    # try to get entry from DB
    afm = C3sMember.get_by_code(refcode)
    if isinstance(afm, NoneType):  # no entry?
        #print "entry not found"
        return {
            'confirmed': False,
            'firstname': 'foo',
            'lastname': 'bar',
            'result_msg': 'bad URL / bad codes. please contact office@c3s.cc!',
        }
    # check token
    if ('_used' in afm.email_confirm_token):  # token was invalidated already
        #print "the token is empty"
        return {
            'confirmed': False,
            'firstname': afm.firstname,
            'lastname': afm.lastname,
            'result_msg': 'your token is invalid. please contact office@c3s.cc!',
        }

    try:
        assert(afm.email_confirm_token in token)
        assert(token in afm.email_confirm_token)
        assert(afm.email in user_email)
        assert(user_email in afm.email)
    except:
        return {
            'confirmed': False,
            'firstname': 'foo',
            'lastname': 'bar',
            'result_msg': 'bad token/email. please contact office@c3s.cc!',
        }

    afm.email_is_confirmed = True
    afm.email_confirm_token += u'_used'
    DBSession.flush()
    # notify staff
    message = Message(
        subject='[C3S Yes!] afm email confirmed',
        sender='noreply@c3s.cc',
        recipients=[request.registry.settings['c3smembership.mailaddr'], ],
        body=u'see {}/detail/{}'.format(
            request.registry.settings['c3smembership.url'],
            afm.id)
    )
    mailer = get_mailer(request)
    mailer.send(message)
    return {
        'confirmed': True,
        'firstname': afm.firstname,
        'lastname': afm.lastname,
        'result_msg': u'',
    }


@view_config(permission='manage',
             route_name='mail_mtype_form')
def mail_mtype_fixer_link(request):
    '''
    send email to member to set her membership type details by visiting a form
    '''
    afmid = request.matchdict['afmid']
    afm = C3sMember.get_by_id(afmid)
    if isinstance(afm, NoneType):
        request.session.flash(
            'id not found. no mail sent.',
            'messages')
        return HTTPFound(request.route_url('dashboard',
                                           number=request.cookies['on_page'],
                                           order=request.cookies['order'],
                                           orderby=request.cookies['orderby']))

    import random
    import string
    _looong_token = u''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in range(13))
    _url = (request.registry.settings['c3smembership.url'] +
            '/mtype/' + afm.email_confirm_code +
            '/' + _looong_token + '/' + afm.email)

    from .mail_mtype_util import make_mtype_email_body
    _body = make_mtype_email_body(afm, _url)

    log.info("mailing membership status form link to AFM # %s" % afm.id)

    if afm.locale == 'de':
        _subject = u'[C3S] Hilfe benötigt: Dein Mitgliedschaftsstatus'
    else:
        _subject = u'[C3S] Help needed: Your Membership Status'

    message = Message(
        subject=_subject,
        sender='yes@c3s.cc',
        recipients=[
            afm.email,
            request.registry.settings['c3smembership.mailaddr']],
        body=_body
    )
    #print(message.subject)
    #print(message.body)
    mailer = get_mailer(request)
    mailer.send(message)
    afm.mtype_confirm_token = _looong_token
    afm.mtype_email_date = datetime.now()
    afm.membership_type = u'pending'
    return HTTPFound(request.route_url('dashboard',
                                       number=request.cookies['on_page'],
                                       order=request.cookies['order'],
                                       orderby=request.cookies['orderby']) +
                     '#member_' + str(afm.id))


@view_config(renderer='templates/mtype-form.pt',
             route_name='mtype_form')
def membership_status_fixer(request):
    '''
    let member confirm her email membership details by filling a form
    '''
    user_email = request.matchdict['email']
    refcode = request.matchdict['refcode']
    token = request.matchdict['token']
    # try to get entry from DB
    afm = C3sMember.get_by_code(refcode)
    if isinstance(afm, NoneType):  # no entry?
        #print "entry not found"
        request.session.flash(
            'bad URL / bad codes. please contact office@c3s.cc!',
            'message_above_form'
        )
        return {
            'form': '',
            'confirmed': False,
            'firstname': 'foo',
            'lastname': 'bar',
            'result_msg': 'bad URL / bad codes. please contact office@c3s.cc!',
        }
    # check token
    #if isinstance(afm.mtype_confirm_token, NoneType):
    #    #request.session.flash('no ')
    #    #return HTTPFound(request.route_url('dashboard_only'))
    # check token even more
    if (len(afm.mtype_confirm_token) == 0) or (
            afm.mtype_confirm_token.endswith('_used')):
        # token was invalidated already
        #    #print "the token is empty"
        request.session.flash(
            'your token is invalid. please contact office@c3s.cc!',
            'message_above_form'
        )
        return {
            'form': '',
            'confirmed': False,
    #        'firstname': afm.firstname,
    #        'lastname': afm.lastname,
            'result_msg': 'your token is invalid. please contact office@c3s.cc!',
        }

    try:
        print "token: {}".format(token)
        assert(afm.mtype_confirm_token in token)
        assert(token in afm.mtype_confirm_token)
        assert(afm.email in user_email)
        assert(user_email in afm.email)
    except:
        request.session.flash(
            'bad token/email. please contact office@c3s.cc!',
            'message_above_form')
        return {
            'form': '',
            'confirmed': False,
            #         'firstname': 'foo',
            #         'lastname': 'bar',
            'result_msg': 'bad token/email. please contact office@c3s.cc!',
        }

    # construct a form
    class MembershipInfo(colander.Schema):
        yes_no = ((u'yes', _(u'Yes')),
                  (u'no', _(u'No')))
        membership_type = colander.SchemaNode(
            colander.String(),
            title=_(u'I want to become a ... (choose '
                    'membership type, see C3S SCE statute sec. 4)'),
            description=_(u'choose the type of membership.'),
            widget=deform.widget.RadioChoiceWidget(
                values=(
                    (u'normal',
                     _(u'FULL member. Full members have to be natural persons '
                       'who register at least three works with C3S they '
                       'created themselves. This applies to composers, '
                       'lyricists and remixers. They get a vote.')),
                    (u'investing',
                     _(u'INVESTING member. Investing members can be natural '
                       'or legal entities or private companies that do not '
                       'register works with C3S. They do not get a vote, '
                       'but may counsel.'))
                ),
            ),
            oid="mtype",
        )
        member_of_colsoc = colander.SchemaNode(
            colander.String(),
            title=_(
                u'Currently, I am a member of (at least) one other '
                'collecting society.'),
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
        )

    class MembershipForm(colander.Schema):
        """
        The Form consists of
        - Membership Information
        """
        membership_info = MembershipInfo(
            title=_(u"Membership Requirements")
        )

    schema = MembershipForm()

    form = deform.Form(
        schema,
        buttons=[
            deform.Button('submit', _(u'Submit')),
            deform.Button('reset', _(u'Reset'))
        ],
        #use_ajax=True,
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
            #print("the controls from the form: %s \n") % controls
            #for thing in appstruct:
            #    print("the thing: %s") % thing
            #    print("type: %s") % type(thing)
            #print(e)
            #message.append(
            request.session.flash(
                _(u"Please note: There were errors, "
                  "please check the form below."),
                'message_above_form',
                allow_duplicate=False)
            return{
                'confirmed': True,
                'form': e.render()}
        # all good, store the information
        afm.membership_type = appstruct['membership_info']['membership_type']
        #print 'afm.membership_type: {}'.format(afm.membership_type)
        afm.member_of_colsoc = (
            appstruct['membership_info']['member_of_colsoc'] == u'yes')
        #print 'afm.member_of_colsoc: {}'.format(afm.member_of_colsoc)
        afm.name_of_colsoc = appstruct['membership_info']['name_of_colsoc']
        #print 'afm.name_of_colsoc: {}'.format(afm.name_of_colsoc)

        # remove old messages from the session
        request.session.pop_flash()

        # invalidate token
        afm.mtype_confirm_token += u'_used'
        # # notify staff
        message = Message(
            subject='[C3S Yes!] membership status confirmed',
            sender='noreply@c3s.cc',
            recipients=[
                request.registry.settings['c3smembership.mailaddr'],
            ],
            body=u'see {}/detail/{}'.format(
                request.registry.settings['c3smembership.url'],
                afm.id)
        )
        mailer = get_mailer(request)
        mailer.send(message)

        return HTTPFound(request.route_url('mtype_thanks'))

    # render the form in a template
    html = form.render()

    return {
        'form': html,
        'confirmed': True,
    }


@view_config(renderer='templates/mtype-thanks.pt',
             route_name='mtype_thanks')
def membership_status_thanks(request):
    '''
    say thanks
    '''
    return {'foo': 'bar'}