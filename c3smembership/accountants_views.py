# -*- coding: utf-8 -*-
import tempfile
import unicodecsv

from c3smembership.models import (
    C3sMember,
    C3sStaff,
    DBSession,
)
from c3smembership.utils import generate_pdf
from c3smembership.mail_utils import (
    make_signature_confirmation_emailbody,
    make_payment_confirmation_emailbody
)
from pkg_resources import resource_filename
import colander
import deform
from deform import ValidationFailure

from pyramid.i18n import (
    get_localizer,
)
from pyramid.view import view_config
from pyramid.threadlocal import get_current_request
from pyramid.httpexceptions import HTTPFound
from pyramid.security import (
    remember,
    forget,
    authenticated_userid,
)
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from pyramid.url import route_url
from translationstring import TranslationStringFactory
from datetime import datetime
from sqlalchemy.exc import (
    IntegrityError,
    ResourceClosedError,
)
import math

deform_templates = resource_filename('deform', 'templates')
c3smembership_templates = resource_filename('c3smembership', 'templates')

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


@view_config(renderer='templates/login.pt',
             route_name='login')
def accountants_login(request):
    """
    This view lets accountants log in.
    if a person is already logged in, she is forwarded to the dashboard
    """
    logged_in = authenticated_userid(request)
    #print("authenticated_userid: " + str(logged_in))

    log.info("login by %s" % logged_in)

    if logged_in is not None:  # if user is already authenticated
        return HTTPFound(  # redirect her to the dashboard
            request.route_url('dashboard_only'))

    class AccountantLogin(colander.MappingSchema):
        """
        colander schema for login form
        """
        login = colander.SchemaNode(
            colander.String(),
            title=_(u"login"),
            oid="login",
        )
        password = colander.SchemaNode(
            colander.String(),
            validator=colander.Length(min=5, max=100),
            widget=deform.widget.PasswordWidget(size=20),
            title=_(u"password"),
            oid="password",
        )

    schema = AccountantLogin()

    form = deform.Form(
        schema,
        buttons=[
            deform.Button('submit', _(u'Submit')),
            deform.Button('reset', _(u'Reset'))
        ],
        #use_ajax=True,
        #renderer=zpt_renderer
    )

    # if the form has been used and SUBMITTED, check contents
    if 'submit' in request.POST:
        #print("the form was submitted")
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure, e:
            print(e)

            request.session.flash(
                _(u"Please note: There were errors, "
                  "please check the form below."),
                'message_above_form',
                allow_duplicate=False)
            return{'form': e.render()}

        # get user and check pw...
        login = appstruct['login']
        password = appstruct['password']

        try:
            checked = C3sStaff.check_password(login, password)
        except AttributeError:  # pragma: no cover
            checked = False
        if checked:
            log.info("password check for %s: good!" % login)
            headers = remember(request, login)
            log.info("logging in %s" % login)
            return HTTPFound(  # redirect to accountants dashboard
                location=route_url(  # after successful login
                    'dashboard_only',
                    request=request),
                headers=headers)
        else:
            log.info("password check: failed.")

    html = form.render()
    return {'form': html, }


@view_config(renderer='templates/import.pt',
             permission='manage',
             route_name='import_all')
def import_db(request):
    """
    import the contents of import.csv to the database
    """
    try:  # check if the file exists
        with open('import/import.csv', 'r') as f:
            # store contents in tempfile
            content = tempfile.NamedTemporaryFile()
            content.write(f.read())
            content.seek(0)  # rewind to beginning

    except IOError, ioe:
        print ioe
        return {'message': "file not found.",
                #        'codes': ''
                }
    # reader for CSV files
    r = unicodecsv.reader(content.file, delimiter=';',
                          encoding='utf-8',
                          quoting=unicodecsv.QUOTE_ALL
                          )
    header = r.next()  # first line is the header.
    #print("the header: %s" % header)
    # check it for compatibility
    try:
        assert header == [
            u'firstname', u'lastname', u'email',  # 0, 1, 2
            u'password', u'last_password_change',  # 3, 4
            u'address1', u'address2', u'postcode', u'city', u'country',  # 5-9
            u'locale', u'date_of_birth',  # 10, 11
            u'email_is_confirmed', u'email_confirm_code',  # 12, 13
            u'num_shares', u'date_of_submission',  # 14, 15
            u'membership_type',  # 16
            u'member_of_colsoc', u'name_of_colsoc',  # 17, 18
            u'signature_received', u'signature_received_date',  # 19, 20
            u'payment_received', u'payment_received_date',  # 21, 22
            u'signature_confirmed', u'signature_confirmed_date',  # 23, 24
            u'payment_confirmed', u'payment_confirmed_date',  # 25, 26
            u'accountant_comment'  # 27
        ]
    except AssertionError, ae:
        print ae
        print "the header of the CSV does not match what we expect"
        return {'message': "header fields mismatch. NOT importing",
                #'codes': _codes,
                }

    # remember the codes imported
    # _codes = []

    # count the datasets
    counter = 0

    while True:
        # import pdb
        # pdb.set_trace()
        try:
            row = r.next()
        except:
            break
        counter += 1
        #print("=== row %s: %s" % (counter, row))
        #print("=== DEBUG: row[12] is: %s " % row[12])
        #print("=== DEBUG: row[15] is: %s " % row[15])
        # DEBUGGING (show datasets):
        #for i in range(row.__len__()):
        #    print('%s header: %s row: %s' % (i, header[i], row[i]))
#
#
# (Pdb) for i in range(row.__len__()): print('%s header: %s row: %s' % (i, header[i], row[i]))
# 0 header: firstname row: Firstnäme
# 1 header: lastname row: Lastname
# 2 header: email row: foo@shri.de
# 3 header: password row: $2a$10$gv8NJbKfuPuOt9GYn1/bxeW3vNLVkPlD3FQEOJ8iioWraMMKX9h4K
# 4 header: last_password_change row: 2013-11-14 10:41:14.000425
# 5 header: address1 row: address one
# 6 header: address2 row: address two
# 7 header: postcode row: 12345 foo
# 8 header: city row: Footown Mäh
# 9 header: country row: Foocountry
# 10 header: locale row: DE
# 11 header: date_of_birth row: 2013-11-14
# 12 header: email_is_confirmed row: True
# 13 header: email_confirm_code row: ABCDEFGHIJ
# 14 header: num_shares row: 10
# 15 header: date_of_submission row: 2013-11-14 10:41:14.000506
# 16 header: membership_type row: normal
# 17 header: member_of_colsoc row: True
# 18 header: name_of_colsoc row: GEMA
# 19 header: signature_received row: False
# 20 header: signature_received_date row: 1970-01-01 00:00:00
# 21 header: payment_received row: False
# 22 header: payment_received_date row: 1970-01-01 00:00:00
# 23 header: signature_confirmed row: True
# 24 header: signature_confirmed_date row: 2014-01-04 23:22:02.652407
# 25 header: payment_confirmed row: True
# 26 header: payment_confirmed_date row: 2013-12-11 20:19:53.365248
# 27 header: accountant_comment row:

        #import pdb
        #pdb.set_trace()
        #print(row[12] is True)

        import_member = C3sMember(
            firstname=row[0],
            lastname=row[1],
            email=row[2],
            password=row[3],
            address1=row[5],
            address2=row[6],
            postcode=row[7],
            city=row[8],
            country=row[9],
            locale=row[10],
            date_of_birth=datetime.strptime(row[11], '%Y-%m-%d'),
            # (1970, 1, 1)
            email_is_confirmed=True if (row[12] == 'True') else False,
            email_confirm_code=row[13],
            date_of_submission=row[15],
            membership_type=row[16],
            member_of_colsoc=True if (row[17] == 'True') else False,
            name_of_colsoc=row[18],
            num_shares=row[14],
        )
        import_member.last_password_change = datetime.strptime(
            row[4], '%Y-%m-%d %H:%M:%S.%f')
        import_member.date_of_submission = datetime.strptime(
            row[15], '%Y-%m-%d %H:%M:%S.%f')
        import_member.signature_received = True if (
            row[19] == 'True') else False
        try:
            import_member.signature_received_date = datetime.strptime(
                row[20], '%Y-%m-%d %H:%M:%S.%f')
        except:
            import_member.signature_received_date = datetime.strptime(
                row[20], '%Y-%m-%d %H:%M:%S')
        import_member.payment_received = True if (row[21] == 'True') else False
        try:
            import_member.payment_received_date = datetime.strptime(
                row[22], '%Y-%m-%d %H:%M:%S')
        except:
            import_member.payment_received_date = datetime.strptime(
                row[22], '%Y-%m-%d %H:%M:%S.%f')
        import_member.signature_confirmed = True if (
            row[23] == 'True') else False
        try:
            import_member.signature_confirmed_date = datetime.strptime(
                row[24], '%Y-%m-%d %H:%M:%S')
        except:
            import_member.signature_confirmed_date = datetime.strptime(
                row[24], '%Y-%m-%d %H:%M:%S.%f')

        import_member.payment_confirmed = True if (
            'True' in row[25]) else False
        try:
            import_member.payment_confirmed_date = datetime.strptime(
                row[26], '%Y-%m-%d %H:%M:%S')
        except:
            import_member.payment_confirmed_date = datetime.strptime(
                row[26], '%Y-%m-%d %H:%M:%S.%f')

        import_member.accountant_comment = row[27]
        print('importing %s now...' % counter)
        try:
            dbsession = DBSession
            dbsession.add(import_member)
            dbsession.flush()
            log.info(
                "%s imported dataset %s" % (
                    authenticated_userid(request),
                    import_member.email_confirm_code))
            print('done with %s!' % counter)
        except ResourceClosedError, rce:
            # XXX can't catch this exception,
            # because it happens somwhere else, later, deeper !?!
            print "transaction was aborted/resource closed"
            print rce
            return {'message': "tried import of dataset(s) with existing confirm code. ABORTED!"}
        except IntegrityError, ie:
            print "integrity error"
            dbsession.rollback()
            print ie
            if 'column email_confirm_code is not unique' in ie.message:
                print("import of dataset %s failed, because the confirmation"
                      "code already existed" % counter)
                return {'message': "tried import of dataset(s) with existing confirm code. ABORTED!"}
        except StopIteration, si:
            print "stop iteration reached"
            print si
            return {'message': "file found, StopIteration reached."}
        #except:
        #    print "passing"
        #    pass

    print("done with all import steps, successful or not!")
    return HTTPFound(
        request.route_url('dashboard_only'))
                # _codes.append(row[13])
                # print("the codes: %s" % str(_codes))

    # except StopIteration, si:
    #     print si
    #     print("counter: %s" % counter)
    #     return {'message': "file found. import complete",
    #             #'codes': _codes,
    #             }


@view_config(renderer='csv',
             permission='manage',
             route_name='export_all')
def export_db(request):
    """
    export the database to a CSV file
    """
    datasets = C3sMember.member_listing(
        "id", how_many=C3sMember.get_number(), order='asc')
    header = ['firstname', 'lastname', 'email',
              'password', 'last_password_change',
              'address1', 'address2', 'postcode', 'city', 'country',
              'locale', 'date_of_birth',
              'email_is_confirmed', 'email_confirm_code',
              'num_shares', 'date_of_submission',
              'membership_type',
              'member_of_colsoc', 'name_of_colsoc',
              'signature_received', 'signature_received_date',
              'payment_received', 'payment_received_date',
              'signature_confirmed', 'signature_confirmed_date',
              'payment_confirmed', 'payment_confirmed_date',
              'accountant_comment',
              ]
    rows = []  # start with empty list
    for m in datasets:
        rows.append(
            (m.firstname, m.lastname, m.email,
             m.password, m.last_password_change,
             m.address1, m.address2, m.postcode, m.city, m.country,
             m.locale, m.date_of_birth,
             m.email_is_confirmed, m.email_confirm_code,
             m.num_shares, m.date_of_submission,
             m.membership_type,
             m.member_of_colsoc, m.name_of_colsoc,
             m.signature_received, m.signature_received_date,
             m.payment_received, m.payment_received_date,
             m.signature_confirmed, m.signature_confirmed_date,
             m.payment_confirmed, m.payment_confirmed_date,
             m.accountant_comment)
        )
    return {
        'header': header,
        'rows': rows}


@view_config(renderer='templates/dashboard.pt',
             permission='manage',
             route_name='dashboard')
def accountants_desk(request):
    """
    This view lets accountants view applications and set their status:
    has their signature arrived? how about the payment?
    """
    _number_of_datasets = C3sMember.get_number()
    try:  # check if page number, orderby and order were supplied with the URL
        _page_to_show = int(request.matchdict['number'])
        _order_by = request.matchdict['orderby']
        _order = request.matchdict['order']
    except:
        print("Using default values")
        _page_to_show = 0
        _order_by = 'id'
        _order = 'asc'

    # check for input from "find dataset by confirm code" form
    if 'code_to_show' in request.POST:
        try:
            _code = request.POST['code_to_show']
            log.info(
                "%s searched for code %s" % (
                    authenticated_userid(request), _code))
            _entry = C3sMember.get_by_code(_code)

            return HTTPFound(
                location=request.route_url(
                    'detail',
                    memberid=_entry.id)
            )
        except:
            pass

    """
    num_display determines how many items are to be shown on one page
    """
    if 'num_to_show' in request.POST:
        try:
            _num = int(request.POST['num_to_show'])
            if isinstance(_num, type(1)):
                num_display = _num
        except:
            # choose default
            num_display = 20
    elif 'num_display' in request.cookies:
        #print("found it in cookie")
        num_display = int(request.cookies['num_display'])
    else:
        #print("setting default")
        num_display = request.registry.settings[
            'c3smembership.dashboard_number']

    """
    base_offset helps us to minimize impact on the database
    when querying for results.
    we can choose just those results we need for the page to show
    """
    base_offset = int(_page_to_show) * int(num_display)

    # get data sets from DB

    _members = C3sMember.member_listing(
        _order_by, how_many=num_display, offset=base_offset, order=_order)

    # calculate next-previous-navi
    next_page = (int(_page_to_show) + 1)
    if (int(_page_to_show) > 0):
        previous_page = int(_page_to_show) - 1
    else:
        previous_page = int(_page_to_show)
    _last_page = int(math.ceil(_number_of_datasets / int(num_display)))
    if next_page > _last_page:
        next_page = _last_page
    # store info about current page in cookie
    request.response.set_cookie('on_page', value=str(_page_to_show))
    request.response.set_cookie('num_display', value=str(num_display))
    request.response.set_cookie('order', value=str(_order))
    request.response.set_cookie('orderby', value=str(_order_by))



    _message = None
    if 'message' in request.GET:
        _message = request.GET['message']

    return {'_number_of_datasets': _number_of_datasets,
            'members': _members,
            'num_display': num_display,
            'next': next_page,
            'previous': previous_page,
            'current': _page_to_show,
            'orderby': _order_by,
            'order': _order,
            'message': _message,
            'last_page': _last_page,
            'is_last_page': _page_to_show == _last_page,
            'is_first_page': _page_to_show == 0,
            }


@view_config(permission='manage',
             route_name='switch_sig')
def switch_sig(request):
    """
    This view lets accountants switch member signature info
    has their signature arrived?
    """
    memberid = request.matchdict['memberid']
    #log.info("the id: %s" % memberid)

    # store the dashboard page the admin came from
    dashboard_page = request.cookies['on_page']
    order = request.cookies['order']
    order_by = request.cookies['orderby']

    _member = C3sMember.get_by_id(memberid)
    if _member.signature_received is True:
        _member.signature_received = False
        _member.signature_received_date = datetime(1970, 1, 1)
    elif _member.signature_received is False:
        _member.signature_received = True
        _member.signature_received_date = datetime.now()

    log.info(
        "signature status of member.id %s changed by %s to %s" % (
            _member.id,
            request.user.login,
            _member.signature_received
        )
    )

    return HTTPFound(
        request.route_url('dashboard',
                          number=dashboard_page, order=order, orderby=order_by))


@view_config(permission='manage',
             route_name='delete_entry')
def delete_entry(request):
    """
    This view lets accountants delete entries (doublettes)
    """
    memberid = request.matchdict['memberid']
    _member = C3sMember.get_by_id(memberid)

    C3sMember.delete_by_id(_member.id)
    log.info(
        "member.id %s was deleted by %s" % (
            _member.id,
            request.user.login,
        )
    )
    return HTTPFound(
        request.route_url('dashboard_only',  _query={'message': 'Member with id {0} was deleted.'.format(memberid)}))


@view_config(permission='manage',
             route_name='switch_pay')
def switch_pay(request):
    """
    This view lets accountants switch member signature info
    has their signature arrived?
    """
    memberid = request.matchdict['memberid']
    dashboard_page = request.cookies['on_page']
    order = request.cookies['order']
    order_by = request.cookies['orderby']
    _member = C3sMember.get_by_id(memberid)

    if _member.payment_received is True:  # change to NOT SET
        _member.payment_received = False
        _member.payment_received_date = datetime(1970, 1, 1)
    elif _member.payment_received is False:  # set to NOW
        _member.payment_received = True
        _member.payment_received_date = datetime.now()

    log.info(
        "payment info of member.id %s changed by %s to %s" % (
            _member.id,
            request.user.login,
            _member.payment_received
        )
    )
    return HTTPFound(
        request.route_url('dashboard',
                          number=dashboard_page, order=order, orderby=order_by))


@view_config(renderer='templates/detail.pt',
             permission='manage',
             route_name='detail')
def member_detail(request):
    """
    This view lets accountants view member details
    has their signature arrived? how about the payment?
    """
    logged_in = authenticated_userid(request)
    #log.info("detail view.................................................")
    print("---- authenticated_userid: " + str(logged_in))

    # this following stanza is overridden by the views permission settings
    #if logged_in is None:  # not authenticated???
    #    return HTTPFound(  # go back to login!!!
    #        location=route_url(
    #            'login',
    #            request=request),
    #    )

    memberid = request.matchdict['memberid']
    #log.info("the id: %s" % memberid)

    _member = C3sMember.get_by_id(memberid)

    #print(_member)
    if _member is None:  # that memberid did not produce good results
        return HTTPFound(  # back to base
            request.route_url('dashboard_only'))

    class ChangeDetails(colander.MappingSchema):
        """
        colander schema (form) to change details of member
        """
        signature_received = colander.SchemaNode(
            colander.Bool(),
            title=_(u"Have we received a good signature?")
        )
        payment_received = colander.SchemaNode(
            colander.Bool(),
            title=_(u"Have we received payment for the shares?")
        )

    schema = ChangeDetails()
    form = deform.Form(
        schema,
        buttons=[
            deform.Button('submit', _(u'Submit')),
            deform.Button('reset', _(u'Reset'))
        ],
        use_ajax=True,
        renderer=zpt_renderer
    )

    # if the form has been used and SUBMITTED, check contents
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure, e:  # pragma: no cover
            log.info(e)
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

        # change info about member in database

        test1 = (  # changed value through form (different from db)?
            appstruct['signature_received'] == _member.signature_received)
        if not test1:
            log.info(
                "info about signature of %s changed by %s to %s" % (
                    _member.id,
                    request.user.login,
                    appstruct['signature_received']))
            _member.signature_received = appstruct['signature_received']
        test2 = (  # changed value through form (different from db)?
            appstruct['payment_received'] == _member.payment_received)
        if not test2:
            log.info(
                "info about payment of %s changed by %s to %s" % (
                    _member.id,
                    request.user.login,
                    appstruct['payment_received']))
            _member.payment_received = appstruct['payment_received']
        # store appstruct in session
        request.session['appstruct'] = appstruct

        # show the updated details
        HTTPFound(route_url('detail', request, memberid=memberid))

    # else: form was not submitted: just show member info and form
    else:
        appstruct = {  # populate form with values from DB
            'signature_received': _member.signature_received,
            'payment_received': _member.payment_received}
        form.set_appstruct(appstruct)
        #print("the appstruct: %s") % appstruct
    html = form.render()

    return {'member': _member,
            'form': html}


@view_config(permission='view',
             route_name='logout')
def logout_view(request):
    """
    can be used to log a user/staffer off. "forget"
    """
    request.session.invalidate()
    request.session.flash(u'Logged out successfully.')
    headers = forget(request)
    return HTTPFound(location=route_url('login', request),
                     headers=headers)


@view_config(permission='manage',
             route_name='regenerate_pdf')
def regenerate_pdf(request):
    """
    staffers can regenerate a users pdf
    """
    _code = request.matchdict['code']
    _member = C3sMember.get_by_code(_code)

    if _member is None:  # that memberid did not produce good results
        return HTTPFound(  # back to base
            request.route_url('dashboard_only'))
    _appstruct = {
        'firstname': _member.firstname,
        'lastname': _member.lastname,
        'address1': _member.address1,
        'address2': _member.address2,
        'postcode': _member.postcode,
        'city': _member.city,
        'email': _member.email,
        'email_confirm_code': _member.email_confirm_code,
        'country': _member.country,
        '_LOCALE_': _member.locale,
        'membership_type': _member.membership_type,
        'num_shares': _member.num_shares,
        'date_of_birth': _member.date_of_birth,
        'date_of_submission': _member.date_of_submission,
    }
    log.info(
        "%s regenerated the PDF for code %s" % (
            authenticated_userid(request), _code))
    return generate_pdf(_appstruct)


@view_config(permission='manage',
             route_name='mail_sig_confirmation')
def mail_signature_confirmation(request):
    """
    send a mail to membership applicant
    informing her about reception of signature
    """
    _id = request.matchdict['memberid']
    _member = C3sMember.get_by_id(_id)

    message = Message(
        subject=_('[C3S AFM] We have received your signature. Thanks!'),
        sender='yes@c3s.cc',
        recipients=[_member.email],
        body=make_signature_confirmation_emailbody(_member)
    )
    #print(message.body)
    mailer = get_mailer(request)
    mailer.send(message)
    _member.signature_confirmed = True
    _member.signature_confirmed_date = datetime.now()
    return HTTPFound(request.route_url('dashboard',
                                       number=request.cookies['on_page'],
                                       order=request.cookies['order'],
                                       orderby=request.cookies['orderby'])
                     )


@view_config(permission='manage',
             route_name='mail_pay_confirmation')
def mail_payment_confirmation(request):
    """
    send a mail to membership applicant
    informing her about reception of payment
    """
    _id = request.matchdict['memberid']
    _member = C3sMember.get_by_id(_id)

    message = Message(
        subject=_('[C3S AFM] We have received your payment. Thanks!'),
        sender='yes@c3s.cc',
        recipients=[_member.email],
        body=make_payment_confirmation_emailbody(_member)
    )
    #print(message.body)
    mailer = get_mailer(request)
    mailer.send(message)
    _member.payment_confirmed = True
    _member.payment_confirmed_date = datetime.now()
    return HTTPFound(request.route_url('dashboard',
                                       number=request.cookies['on_page'],
                                       order=request.cookies['order'],
                                       orderby=request.cookies['orderby'],
                                       )
                     )


@view_config(permission='manage', route_name='dashboard_only')
def dashboard_only(request):
    if 'on_page' in request.cookies:
        try:
            _number = int(request.cookies['on_page'])
        except ValueError:
            _number = 0
    else:
        _number = 0
    if 'orderby' in request.cookies:
        _order_by = request.cookies['orderby']
    else:
        _order_by = 'id'
    if 'order' in request.cookies:
        _order = request.cookies['order']
    else:
        _order = 'asc'
    return HTTPFound(request.route_url('dashboard', number=_number, orderby=_order_by, order=_order, _query=request.GET))