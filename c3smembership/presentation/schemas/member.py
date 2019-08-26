# -*- coding: utf-8 -*-
"""
Member schema definitions
"""

from datetime import date

import colander
import deform

from c3smembership.utils import country_codes
from c3smembership.presentation.i18n import _
from c3smembership.presentation.view_processing import ValidationNode
from c3smembership.utils import locale_codes


COUNTRY_DEFAULT = u'DE'
LOCALE_DEFAULT = u'de'


@colander.deferred
def deferred_dob_validator(node, keywords):
    """
    Deferred date of birth validator

    Needed for testing purposes.
    """
    # The node argument is necessary to confirm to the deferred validator
    # interface. Therefore:

    # pylint: disable=unused-argument
    kw_date = keywords['date']
    return colander.Range(
        min=kw_date(1913, 1, 1),
        # max 18th birthday, no minors through web formular
        max=kw_date(
            kw_date.today().year-18,
            kw_date.today().month,
            kw_date.today().day),
        min_err=_(
            u'Sorry, but we do not believe that the birthday you '
            u'entered is correct.'),
        max_err=_(
            u'Unfortunately, the membership application of an '
            u'underaged person is currently not possible via our web '
            u'form. Please send an email to office@c3s.cc.'))


class PersonalDataBase(colander.MappingSchema):
    """
    Colander schema containing member personal data like name and address
    """

    firstname = colander.SchemaNode(
        colander.String(),
        title=_(u'First Name'),
        oid='firstname',
    )
    lastname = colander.SchemaNode(
        colander.String(),
        title=_(u'Last Name'),
        oid='lastname',
    )
    email = colander.SchemaNode(
        colander.String(),
        title=_(u'Email Address'),
        validator=colander.Email(),
        oid='email',
    )
    address1 = colander.SchemaNode(
        colander.String(),
        title=_(u'Address Line 1'),
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
        widget=deform.widget.DatePartsWidget(),
        default=date(2013, 1, 1),
        validator=deferred_dob_validator,
        oid='date_of_birth',
    )


class PersonalDataJoin(PersonalDataBase):
    """
    Personal data colander schema for member registration

    Includes a password field, used for the join form.
    """
    password = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=5, max=100),
        widget=deform.widget.CheckedPasswordWidget(size=20),
        title=_(u'Password (to protect access to your data)'),
        description=_(u'We need a password to protect your data. After '
                      u'verifying your email you will have to enter it.'),
        oid='password',
    )


class PersonalDataCreateEdit(PersonalDataBase):
    """
    Personal data colander schema for backend creation and editing

    Includes email_is_confirmed flag and locale, used to create and edit
    members by staff.
    """
    date_of_birth = colander.SchemaNode(
        colander.Date(),
        title=_(u'Date of Birth'),
        default=date(1970, 1, 1),
        oid='date_of_birth',
    )
    email_is_confirmed = colander.SchemaNode(
        colander.String(),
        title=_(u'Email Address Confirmed'),
        widget=deform.widget.RadioChoiceWidget(
            values=(
                (u'yes', _(u'Yes, confirmed')),
                (u'no', _(u'No, not confirmed')),)),
        missing=False,
        oid='email_is_confirmed',
    )
    locale = colander.SchemaNode(
        colander.String(),
        title=_(u'Preferred Language'),
        widget=deform.widget.SelectWidget(
            values=locale_codes),
        missing=u'',
    )


class MemberNode(ValidationNode):
    """
    Define a Colander schema node for member by membership number

    The schema node validates a membership number and transforms it into a
    member object.
    """

    schema_type = colander.Int
    validation_error_message = 'Membership number {} does not exist.'
    new_name = 'member'

    def transform(self, request, value):
        """
        Transform the validated membership number into a member object
        """
        return request.registry.member_information.get_member(value)


class MemberIdNode(ValidationNode):
    """
    Define a Colander schema node for member by member ID

    The schema node validates a membership id and transforms it into a member
    object.

    The schema node only exists for legacy reasons. The presentation layer
    should not deal with database IDs but with the business keys instead which
    is the membership number for which the MemberNode class exists.
    """

    schema_type = colander.Int
    validation_error_message = 'Member ID {} does not exist.'
    new_name = 'member'

    def transform(self, request, value):
        """
        Transform the validated member ID into a member object
        """
        return request.registry.member_information.get_member_by_id(value)


class MemberIdIsMemberNode(MemberIdNode):
    """
    Define a Colander schema node for member with membership by member ID

    The schema node validates a membership id, transforms it into a member
    object and verifies that membership was granted.

    The schema node only exists for legacy reasons. The presentation layer
    should not deal with database IDs but with the business keys instead which
    is the membership number for which the MemberNode class exists.
    """

    def validate(self, request, value):
        """
        Validate the transformed value

        Args:
            request: The ``pyramid.request.Request`` which the validated data
                was passed to
            value: The transformed value of the schema node

        Returns:
            Usually None. The validate method can raise ``colander.Invalid``
            exceptions in case of any validation errors. The default
            implementation raises an exception if the value is None using the
            node's validation_error_message attribute and the original value.

            The validation_error_message attribute can be set for a precise
            error message.

            If the method does return something it is used as a error message
            for a ``colander.Invalid`` exception raised.
        """
        # pylint: disable=unused-argument
        super(MemberIdIsMemberNode, self).validate(request, value)
        if not value.is_member():
            message = \
                u'Member with member ID {} has not been granted membership'
            raise colander.Invalid(
                self,
                message.format(self.original_value))


class MemberMatchdict(colander.MappingSchema):
    """
    Schema for validating a membership number matchdict

    The membership number is valid as an integer and turned into a member
    object.
    """

    membership_number = MemberNode()


class MemberIdMatchdict(colander.MappingSchema):
    """
    Schema for validating a member ID matchdict

    The member ID is valid as an integer and turned into a member object.
    """
    member_id = MemberIdNode()


class MailCertificateMatchdict(colander.MappingSchema):
    """
    Schema for validating the mail certificate matchdict

    The member ID has is valid as an integer and turned into a member object.
    """
    member_id = MemberIdIsMemberNode()


class GenerateCertificateMatchdict(colander.MappingSchema):
    """
    Schema for validating the generate certificate matchdict

    The member ID has is valid as an integer and turned into a member object.
    The token is a string.
    """
    member_id = MemberIdIsMemberNode()
    token = colander.SchemaNode(colander.String)
