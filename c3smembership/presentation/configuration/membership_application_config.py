# -*- coding: utf-8 -*-
"""
Pyramid application configuration for membership application.
"""

from c3smembership.data.repository.member_repository import MemberRepository
from c3smembership.business.membership_application import MembershipApplication
from c3smembership.presentation.views.membership_acquisition import (
    dashboard_content_size_provider
)

from c3smembership.presentation.configuration import Configuration


class MembershipApplicationConfig(Configuration):
    """
    Configuration for membership application.
    """

    def configure(self):
        """
        Add the configuration of the module to the Pyramid configuration.
        """
        self.configure_routes()
        self.configure_registry()

    def configure_registry(self):
        """
        Configure the registry to contain the membership application business
        layer.
        """
        membership_application = MembershipApplication(MemberRepository)
        self.config.registry.membership_application = membership_application

        # applications for membership
        self.config.make_pagination_route(
            'dashboard',
            dashboard_content_size_provider,
            sort_property_default='id',
            page_size_default=int(
                self.config.get_settings()
                .get('c3smembership.dashboard_number', 30)))

    def configure_routes(self):
        """
        Configure the membership application routes.
        """
        routes = [
            # Membership application process
            # Step 1 (join.pt): home is /, the membership application form
            ('join', '/'),
            # Step 2 (success.pt): check and edit data
            ('success', '/success'),
            # Step 3 email was sent (check-mail.pt): send verification email
            # address
            ('success_check_email', '/check_email'),
            # Still step 3 (verify_password.pt): enter password
            # and step 4 (verify_password.pt): download form
            ('verify_email_password', '/verify/{email}/{code}'),  # PDF
            # PDF download of Step 4.
            ('success_pdf', '/C3S_SCE_AFM_{namepart}.pdf'),  # download

            # applications for membership
            ('dashboard', '/dashboard'),

            ('new_member', '/new_member'),

            ('switch_sig', '/switch_sig/{memberid}'),
            ('switch_pay', '/switch_pay/{memberid}'),

            ('mail_sig_confirmation', '/mail_sig_conf/{memberid}'),
            ('regenerate_pdf', '/re_C3S_SCE_AFM_{code}.pdf'),
            ('mail_pay_confirmation', '/mail_pay_conf/{member_id}'),
            ('mail_mail_confirmation', '/mail_mail_conf/{member_id}'),
            ('mail_sig_reminder', '/mail_sig_reminder/{memberid}'),
            ('mail_pay_reminder', '/mail_pay_reminder/{memberid}'),
            ('delete_entry', '/delete/{memberid}'),
            ('delete_afms', '/delete_afms'),

            # applications for membership
            ('afms_awaiting_approval', '/afms_awaiting_approval'),

            # memberships
            ('make_member', '/make_member/{afm_id}'),
            ('merge_member', '/merge_member/{afm_id}/{mid}'),
        ]
        self._add_routes(routes)
