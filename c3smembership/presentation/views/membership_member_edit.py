# -*- coding: utf-8 -*-
"""
Views for editing member data including form generation from schema.
"""

from datetime import date
import logging
from types import NoneType

import colander
from colander import (
    Range,
)
import deform
from deform import ValidationFailure
from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid
from pyramid.view import view_config

from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.utils import (
    country_codes,
    locale_codes
)
from c3smembership.presentation.i18n import (
    _,
    ZPT_RENDERER,
)

COUNTRY_DEFAULT = u'DE'
LOCALE_DEFAULT = u'de'

LOG = logging.getLogger(__name__)


def get_child_position(form, child_node):
    """
    Gets the position of a child node within its form.
    """
    position = 0
    for child in form:
        if child == child_node:
            return position
        position += 1
    return None


@view_config(
    route_name='edit',
    permission='manage',
    renderer='c3smembership.presentation:templates/pages/'
             'membership_member_edit.pt')
def edit_member(request):
    """
    Let staff edit a member entry.
    """
    try:
        _id = request.matchdict['_id']
        assert(isinstance(int(_id), int))
        member = C3sMember.get_by_id(_id)
        if isinstance(member, NoneType):
            return HTTPFound(request.route_url('dashboard'))
    except:
        return HTTPFound(request.route_url('dashboard'))

    # if we have a valid id, we can load a members data from the db
    # and put the data in an appstruct to fill the form
    appstruct = {}
    email_is_confirmed = 'yes' if member.email_is_confirmed else 'no'
    appstruct['person'] = {
        'firstname': member.firstname,
        'lastname': member.lastname,
        'email': member.email,
        'email_is_confirmed': email_is_confirmed,
        'address1': member.address1,
        'address2': member.address2,
        'postcode': member.postcode,
        'city': member.city,
        'country': member.country,
        'date_of_birth': member.date_of_birth,
        'locale': member.locale,
    }

    appstruct['membership_meta'] = {
        'membership_accepted': member.membership_accepted,
        'membership_date': (
            # this is necessary because membership_date's default is
            # 1970-01-01 which should be changed to None in the future
            u''
            if member.membership_date == date(1970, 1, 1)
            else member.membership_date),
        'is_duplicate': member.is_duplicate,
        'is_duplicate_of': (
            u''
            if member.is_duplicate_of is None
            else member.is_duplicate_of),
        'accountant_comment': (
            u''
            if member.accountant_comment is None
            else member.accountant_comment),
        'signature_received': member.signature_received,
        'signature_received_date': member.signature_received_date,
        'payment_received': member.payment_received,
        'payment_received_date': member.payment_received_date,
        'membership_loss_date': member.membership_loss_date,
        'membership_loss_type': (
            u''
            if member.membership_loss_type is None
            else member.membership_loss_type),
    }
    appstruct['membership_info'] = {
        'membership_type': member.membership_type,
        'entity_type': u'legalentity' if member.is_legalentity else 'person',
        'member_of_colsoc': 'yes' if member.member_of_colsoc else 'no',
        'name_of_colsoc': member.name_of_colsoc,
    }
    membership_loss_types = (
        ('', _(u'(Select)')),
        ('resignation', _(u'Resignation')),
        ('expulsion', _(u'Expulsion')),
        ('death', _(u'Death')),
        ('bankruptcy', _(u'Bankruptcy')),
        ('winding-up', _(u'Winding-up')),
        ('shares_transfer', _(u'Transfer of remaining shares'))
    )

    class PersonalData(colander.MappingSchema):
        """
        Colander schema of the personal data for editing member data.
        """
        firstname = colander.SchemaNode(
            colander.String(),
            title=_(u'(Real) First Name'),
            oid='firstname',
        )
        lastname = colander.SchemaNode(
            colander.String(),
            title=_(u'(Real) Last Name'),
            oid='lastname',
        )
        email = colander.SchemaNode(
            colander.String(),
            title=_(u'Email Address'),
            validator=colander.Email(),
            oid='email',
        )
        email_is_confirmed = colander.SchemaNode(
            colander.String(),
            title=_(u'Email Address Confirmed'),
            widget=deform.widget.RadioChoiceWidget(
                values=(
                    (u'yes', _(u'Yes, confirmed')),
                    (u'no', _(u'No, not confirmed')),)),
            missing=u'',
            oid='email_is_confirmed',
        )

        passwort = colander.SchemaNode(
            colander.String(),
            widget=deform.widget.HiddenWidget(),
            default='NoneSet',
            missing='NoneSetPurposefully'
        )
        address1 = colander.SchemaNode(
            colander.String(),
            title=_(u'Addess Line 1'),
        )
        address2 = colander.SchemaNode(
            colander.String(),
            missing=u'',
            title=_(u'Address Line 2'),
        )
        postcode = colander.SchemaNode(
            colander.String(),
            title=_(u'Postal Code'),
            oid='postcode'
        )
        city = colander.SchemaNode(
            colander.String(),
            title=_(u'City'),
            oid='city',
        )
        country = colander.SchemaNode(
            colander.String(),
            title=_(u'Country'),
            default=COUNTRY_DEFAULT,
            widget=deform.widget.SelectWidget(
                values=country_codes),
            oid='country',
        )
        date_of_birth = colander.SchemaNode(
            colander.Date(),
            title=_(u'Date of Birth'),
            default=date(2013, 1, 1),
            oid='date_of_birth',
        )
        locale = colander.SchemaNode(
            colander.String(),
            title=_(u'Locale'),
            widget=deform.widget.SelectWidget(
                values=locale_codes),
            missing=u'',
        )

    @colander.deferred
    def membership_loss_date_widget(node, keywords):
        """
        Returns a text or hidden input depending on the value of
        membership_accepted within the keywords.
        """
        if keywords.get('membership_accepted'):
            return deform.widget.DateInputWidget()
        else:
            return deform.widget.HiddenWidget()

    @colander.deferred
    def membership_loss_type_widget(node, keywords):
        """
        Returns a select or hidden input depending on the value of
        membership_accepted within the keywords.
        """
        if keywords.get('membership_accepted'):
            return deform.widget.SelectWidget(values=membership_loss_types)
        else:
            return deform.widget.HiddenWidget()

    class MembershipMeta(colander.Schema):
        """
        Colander schema of the meta data for editing member data.
        """
        membership_accepted = colander.SchemaNode(
            colander.Boolean(),
            title=_(u'Membership Accepted')
        )
        membership_date = colander.SchemaNode(
            colander.Date(),
            title=_(u'Membership Acceptance Date'),
            validator=Range(
                min=date(2013, 9, 24),
                max=date.today(),
                min_err=_(u'${val} is earlier than earliest date ${min}.'),
                max_err=_(u'${val} is later than latest date ${max}.')
            ),
            missing=date(1970, 1, 1),
            oid='membership_date',
        )
        is_duplicate = colander.SchemaNode(
            colander.Boolean(),
            title=_(u'Is Duplicate'),
            oid='is_duplicate',
        )
        is_duplicate_of = colander.SchemaNode(
            colander.String(),
            title=_(u'Duplicate Id'),
            missing=u'',
            oid='duplicate_of',
        )
        signature_received = colander.SchemaNode(
            colander.Boolean(),
            title=_(u'Signature Received'),
            oid='signature_received',
        )
        signature_received_date = colander.SchemaNode(
            colander.Date(),
            title=_('Signature reception date'),
            validator=Range(
                min=date(1070, 1, 1),
                max=date.today(),
                min_err=_(u'${val} is earlier than earliest date ${min}.'),
                max_err=_(u'${val} is later than latest date ${max}.')
            ),
            missing=date(1970, 1, 1),
        )
        payment_received = colander.SchemaNode(
            colander.Boolean(),
            title=_(u'Payment Received'),
        )
        payment_received_date = colander.SchemaNode(
            colander.Date(),
            title=_(u'Payment reception date'),
            validator=Range(
                min=date(1970, 1, 1),
                max=date.today(),
                min_err=_(u'${val} is earlier than earliest date ${min}.'),
                max_err=_(u'${val} is later than latest date ${max}.')
            ),
            missing=date(1970, 1, 1),
            oid='_received_date',
        )
        membership_loss_date = colander.SchemaNode(
            colander.Date(),
            widget=membership_loss_date_widget,
            title=_(u'Date of the loss of membership'),
            default=None,
            missing=None,
            oid='membership_loss_date',
        )
        membership_loss_type = colander.SchemaNode(
            colander.String(),
            widget=membership_loss_type_widget,
            title=_(u'Type of membership loss'),
            default=None,
            missing=None,
            oid='membership_loss_type',
        )
        accountant_comment = colander.SchemaNode(
            colander.String(),
            title=_(u'Staff Comment: (255 letters)'),
            missing=u'',
            oid='accountant_comment',
        )

    class MembershipInfo(colander.Schema):
        """
        Colander schema of the additional data for editing member data.
        """
        yes_no = (
            (u'yes', _(u'Yes')),
            (u'no', _(u'No')),
            (u'dontknow', _(u'Unknwon')),
        )

        entity_type = colander.SchemaNode(
            colander.String(),
            title=_(u'Member Category'),
            description=_(u'Please choose the member category.'),
            widget=deform.widget.RadioChoiceWidget(
                values=(
                    (u'person', _(u'Person')),
                    (u'legalentity', _(u'Legal Entity')),
                ),
            ),
            missing=u'',
            oid='entity_type',
        )
        membership_type = colander.SchemaNode(
            colander.String(),
            title=_(u'Type of Membership (C3S Statute § 4)'),
            description=_(u'Please choose the type of membership.'),
            widget=deform.widget.RadioChoiceWidget(
                values=(
                    (u'normal', _(u'Member')),
                    (u'investing', _(u'Investing (non-user) member')),
                    (u'unknown', _(u'Unknown')),
                ),
            ),
            missing=u'',
            oid='membership_type',
        )
        member_of_colsoc = colander.SchemaNode(
            colander.String(),
            title=_('Member of a Collecting Society'),
            widget=deform.widget.RadioChoiceWidget(values=yes_no),
            oid='other_colsoc',
            default=u'',
            missing=u'',
        )
        name_of_colsoc = colander.SchemaNode(
            colander.String(),
            title=_(u'Names of Collecting Societies'),
            description=_(u'Please separate multiple collecting societies by '
                          u'comma.'),
            missing=u'',
            oid='colsoc_name',
        )

    def loss_type_and_date_set_validator(form, value):
        """
        Validates whether the membership loss type is set.

        Membership date and type must both be either set or unset.
        """
        if (value['membership_loss_date'] is None) != \
                (value['membership_loss_type'] is None):
            exc = colander.Invalid(form)
            exc['membership_loss_type'] = \
                _(u'Date and type of membership loss must be set both or '
                  u'none.')
            exc['membership_loss_date'] = \
                _(u'Date and type of membership loss must be set both or '
                  u'none.')
            raise exc

    def loss_date_larger_acceptance_validator(form, value):
        """
        Validates that the membership loss date is not smaller than the
        membership acceptance date.

        As the membership can't be lost before it was granted the membership
        loss date must be larger than the membership acceptance date.
        """
        if (value['membership_loss_date'] is not None and
            (value['membership_loss_date'] < value['membership_date'] or
             not value['membership_accepted'])):
            exc = colander.Invalid(form)
            exc['membership_loss_date'] = \
                _(u'Date membership loss must be larger than membership '
                  u'acceptance date.')
            raise exc

    def loss_date_resignation_validator(form, value):
        """
        Validates that the membership loss date for resignations is the 31st
        of December of any year.

        Resignations are only allowed to the end of the year.
        """
        if (value.get('membership_loss_type', '') == 'resignation' and
            value['membership_loss_date'] is not None and
            not (value['membership_loss_date'].day == 31 and
                 value['membership_loss_date'].month == 12)):
            exc = colander.Invalid(form)
            exc['membership_loss_date'] = \
                _(u'Resignations are only allowed to the 31st of December '
                  u'of a year.')
            raise exc

    class MembershipForm(colander.Schema):
        """
        The form for editing membership information combining all forms for
        the subject areas.
        """
        person = PersonalData(
            title=_(u'Personal Data'),
        )
        membership_meta = MembershipMeta(
            title=_(u'Membership Bureaucracy'),
            validator=colander.All(
                loss_type_and_date_set_validator,
                loss_date_larger_acceptance_validator,
                loss_date_resignation_validator)
        ).bind(
            membership_accepted=member.membership_accepted,
        )
        membership_info = MembershipInfo(
            title=_(u'Membership Requirements')
        )

    def membership_loss_type_entity_type_validator(form, value):
        """
        Validates that only natural persons can have loss type 'death' and
        only legal entites 'winding-up'.
        """
        if (
                value['membership_meta']['membership_loss_type'] == 'death' and
                value['membership_info']['entity_type'] != 'person'):
            exc_type = colander.Invalid(
                form['membership_meta']['membership_loss_type'],
                _(u'The membership loss type \'death\' is only allowed for '
                  u'natural person members and not for legal entity members.'))
            exc_meta = colander.Invalid(form['membership_meta'])
            exc_meta.add(
                exc_type,
                get_child_position(
                    form['membership_meta'],
                    form['membership_meta']['membership_loss_type']))
            exc = colander.Invalid(form)
            exc.add(
                exc_meta,
                get_child_position(
                    form,
                    form['membership_meta']))
            raise exc
        if (
                value['membership_meta'][
                    'membership_loss_type'] == 'winding-up' and
                value['membership_info']['entity_type'] != 'legalentity'):
            exc_type = colander.Invalid(
                form['membership_meta']['membership_loss_type'],
                _(u'The membership loss type \'winding-up\' is only allowed '
                  u'for legal entity members and not for natural person '
                  u'members.'))
            exc_meta = colander.Invalid(form['membership_meta'])
            exc_meta.add(
                exc_type,
                get_child_position(
                    form['membership_meta'],
                    form['membership_meta']['membership_loss_type']))
            exc = colander.Invalid(form)
            exc.add(
                exc_meta,
                get_child_position(
                    form,
                    form['membership_meta']))
            raise exc

    schema = MembershipForm(
        validator=colander.All(
            membership_loss_type_entity_type_validator,
        ))
    form = deform.Form(
        schema,
        buttons=[
            deform.Button('submit', _(u'Submit')),
            deform.Button('reset', _(u'Reset')),
        ],
        renderer=ZPT_RENDERER,
        use_ajax=True,
    )

    def clean_error_messages(error):
        if error.msg is not None and type(error.msg) == list:
            error.msg = list(set(error.msg))
            if None in error.msg:
                error.msg.remove(None)
            if '' in error.msg:
                error.msg.remove('')
            error.msg = ' '.join(list(set(error.msg)))
        for child in error.children:
            clean_error_messages(child)

    # if the form has NOT been used and submitted, remove error messages if
    # any
    if 'submit' not in request.POST:
        request.session.pop_flash()

    # if the form has been used and SUBMITTED, check contents
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure as validationfailure:
            # clean_error_messages(validationfailure.error)
            request.session.flash(
                _(u'Please note: There were errors, '
                  u'please check the form below.'),
                'warning',
                allow_duplicate=False)
            return{'form': validationfailure.render()}

        # to store the data in the DB, the old object is updated
        listing = [  # map data attributes to appstruct items
            ('firstname', appstruct['person']['firstname']),
            ('lastname', appstruct['person']['lastname']),
            ('date_of_birth', appstruct['person']['date_of_birth']),
            ('email', appstruct['person']['email']),
            (
                'email_is_confirmed',
                1 if appstruct['person']['email_is_confirmed'] == 'yes'
                else 0
            ),
            ('address1', appstruct['person']['address1']),
            ('address2', appstruct['person']['address2']),
            ('postcode', appstruct['person']['postcode']),
            ('city', appstruct['person']['city']),
            ('country', appstruct['person']['country']),
            ('locale', appstruct['person']['locale']),
            (
                'membership_date',
                appstruct['membership_meta']['membership_date']
            ),
            ('is_duplicate', appstruct['membership_meta']['is_duplicate']),
            (
                'is_duplicate_of',
                appstruct['membership_meta']['is_duplicate_of']
            ),
            (
                'accountant_comment',
                appstruct['membership_meta']['accountant_comment']
            ),
            (
                'membership_type',
                appstruct['membership_info']['membership_type']
            ),
            (
                'is_legalentity',
                1 if (appstruct['membership_info']['entity_type'] ==
                      'legalentity')
                else 0
            ),
            (
                'name_of_colsoc',
                appstruct['membership_info']['name_of_colsoc']
            ),
            (
                'signature_received',
                appstruct['membership_meta']['signature_received']
            ),
            (
                'signature_received_date',
                appstruct['membership_meta']['signature_received_date']
            ),
            (
                'payment_received',
                appstruct['membership_meta']['payment_received']
            ),
            (
                'payment_received_date',
                appstruct['membership_meta']['payment_received_date']
            ),
            (
                'membership_loss_type',
                appstruct['membership_meta'].get('membership_loss_type', None)
            ),
            (
                'membership_loss_date',
                appstruct['membership_meta'].get('membership_loss_date', None)
            ),
        ]

        for thing in listing:
            attribute_name = thing[0]
            attribute_value = thing[1]

            if member.__getattribute__(attribute_name) == attribute_value:
                pass
            else:
                LOG.info(
                    u'{0} changes {1} of id {2} to {3}'.format(
                        authenticated_userid(request),
                        attribute_name,
                        member.id,
                        attribute_value
                    )
                )
                setattr(member, attribute_name, attribute_value)

        # membership acceptance status can be set or unset.
        if appstruct['membership_meta'][
                'membership_accepted'] == member.membership_accepted:
            pass
        else:
            member.membership_accepted = appstruct[
                'membership_meta']['membership_accepted']
            if isinstance(member.membership_number, NoneType) \
                    and member.membership_accepted:
                member.membership_number = \
                    C3sMember.get_next_free_membership_number()

        if appstruct['membership_info']['entity_type'] == 'legalentity':
            member.is_legalentity = True
        else:
            member.is_legalentity = False

        # empty the messages queue (as validation worked anyways)
        request.session.pop_flash()
        return HTTPFound(  # redirect to details page
            location=request.route_url(
                'detail',
                memberid=member.id),
        )

    form.set_appstruct(appstruct)
    html = form.render()

    return {'form': html}
