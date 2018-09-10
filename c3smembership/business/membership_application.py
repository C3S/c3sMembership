# -*- coding: utf-8 -*-
"""
Provides functionality for the membership application process.
"""

from datetime import (
    datetime,
)
from c3smembership.mail_utils import (
    make_signature_confirmation_email,
    send_message,
)
from pyramid_mailer.message import Message


_make_signature_confirmation_email = make_signature_confirmation_email
_send_message = send_message


class MembershipApplication(object):
    """
    Provides functionality for the membership application process.
    """

    datetime = datetime

    def __init__(self, member_repository):
        """
        Initialises the MembershipApplication object.

        Args:
            member_repository: Object implementing a
                get_member_by_id(member_id) method returning a member objects
                with properties signature_received_date and signature_received.
        """
        self.member_repository = member_repository

    def get(self, member_id):
        """
        Gets membership application information.
        """
        member = self.member_repository.get_member_by_id(member_id)
        return {
            'membership_type': member.membership_type,
            'shares_quantity': member.num_shares,
            'date_of_submission': member.date_of_submission,
            'payment_token': member.email_confirm_code,
        }

    def set_signature_status(self, member_id, signature_status):
        """
        Sets the signature status of the member indicating whether a signed
        contract was received.

        Args:
            member_id (int): The ID of the member of which the signature status
                must be set.
            signature_status (boolean): Boolean value indicating the signature
                status to be set to.
        """
        member = self.member_repository.get_member_by_id(member_id)
        member.signature_received = signature_status
        if signature_status:
            signature_received_date = self.datetime.now()
        else:
            signature_received_date = datetime(1970, 1, 1)
        member.signature_received_date = signature_received_date

    def get_signature_status(self, member_id):
        """
        Gets the signature status of the member's application indicating
        whether a signed contract was received.

        Args:
            member_id (int): The ID of the member of which the signature status
                is requested.

        Returns:
            A boolean value indicating the signature status of the member's
            membership application. True, if a signed contract was received,
            otherwise False.
        """
        member = self.member_repository.get_member_by_id(member_id)
        return member.signature_received

    def set_payment_status(self, member_id, payment_status):
        """
        Sets the payment status of the member indicating whether a signed
        contract was received.

        Args:
            member_id (int): The ID of the member of which the payment status
                must be set.
            signature_status (boolean): Boolean value indicating the payment
                status to be set to.
        """
        member = self.member_repository.get_member_by_id(member_id)
        member.payment_received = payment_status
        if payment_status:
            payment_received_date = self.datetime.now()
        else:
            payment_received_date = datetime(1970, 1, 1)
        member.payment_received_date = payment_received_date

    def get_payment_status(self, member_id):
        """
        Gets the payment status of the member's application indicating whether
        a signed contract was received.

        Args:
            member_id (int): The ID of the member of which the payment status
                is requested.

        Returns:
            A boolean value indicating the payment status of the member's
            membership application. True, if a signed contract was received,
            otherwise False.
        """
        member = self.member_repository.get_member_by_id(member_id)
        return member.payment_received

    def mail_signature_confirmation(self, member_id, request):
        """
        Sends an email to the member in order to confirm that the signed
        contract was received by the C3S.

        Args:
            member_id (int): The ID of the member to which the confirmation
                email is sent.
        """
        # TODO:
        # - Email functionality should be injected to be testable!
        # - Email functionality is an external service which belongs to
        #   cross-cutting concerns.
        # - Emailing service should be independent of the presentation layer,
        #   i.e. independent from pyramid which makes it hard to use
        #   pyramid_mailer.
        # - Resolve request dependency.
        # - Remove dependency to pyramid_mail and move to separate service.
        member = self.member_repository.get_member_by_id(member_id)
        # pylint: disable=too-many-function-args
        email_subject, email_body = _make_signature_confirmation_email(member)
        message = Message(
            subject=email_subject,
            sender=request.registry.settings[
                'c3smembership.notification_sender'],
            recipients=[member.email],
            body=email_body
        )
        # pylint: disable=too-many-function-args
        _send_message(request, message)
        member.signature_confirmed = True
        member.signature_confirmed_date = self.datetime.now()
