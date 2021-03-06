1.31
====


- Add membership dues 2021. As for the previous years the source code has been
  copied, pasted and adjusted for the new year. This is quite a tedious job
  which is caused by the insufficient design for the first year and the lack of
  proper redesign until today.

- Pin docutils due to Sphinx incompatibility

- Fix documentation

- Rely on virtual environment for sphinx-build

- Fix PDF generation testing

- Fix README to always activate the virtual environment

- Remove hard-coded path for database initialization during test

- Small changes regarding signatures due to change of a managing director. Yes,
  still hard-coded. Shame on us.



1.30
====


Add general assembly invitation subject and invitation text editing.



1.29.1
======


- Fix dues balance calculation for invoice note.

- Fix empty dues amount error handling.



1.29
====


- Add membership dues 2020. As for the previous years the source code has been
  copied, pasted and adjusted for the new year. This is quite a tedious job
  which is caused by the insufficient design for the first year and the lack of
  proper redesign until today.

- Rename function to avoid nosetest issue. Nosetests ignores our setup.cfg in
  some conditions, which results in the execution of the function in question
  as test, then causing a following test to fail. renaming the function
  prevents this.

- Fix inconsistent database session use in tests. Database sessions were not
  always closed and therefore apparently closed before opening as a workaround.
  This has been resolved by closing sessions properly. Cleanup like commented
  code and use unittest assertions.

- Fix membership listing validation. The maximum and default date of the
  listing by date form and as well the year list of the listing by year form
  were generated on application start and not dynamically during form
  rendering. This led to the fact that with the turn of the year from 2019 to
  2020 the new year did not appear in the year list and the current date could
  not be entered because it was considered in the past. Now the dates are
  handled dynamically during form rendering.

- Show positive balance in yellow. Balances not equal to zero have been shown
  as red before. This makes it hard to identify rare cases of positive
  balances. Therefore, these are now shown in yellow instead of red.
  Furthermore, the amount is prefixed with a plus sign. Negative balances stay
  red.



1.28.2
======


Fix member certificate downloading from email link. The link did not work and
returned a 500 Internal Server Error.



1.28.1
======


- Adjust chair-person name in email footer.

- Finish cleaning up personal data schema. There were three declarations of
  very similar Colander schemas for personal data including name and address.
  These three can be unified to reduce redundant code and improve test
  coverage.



1.28
====


- Enable invoice archiving for all years. Background archiving can be started
  and the progress observed. It will archive all invoices which are not yet
  archived and do so without relying on a person to specify numbers of invoice
  to be archived or to keep a browser connection alive.

- Retrieve Git version information from outside application path.  The Git
  command for retrieving version information was executed in the working
  directory thus not returning any results or even wrong results when the
  application executed from some other path. Now the Git command is executed
  based on the application path thus returning the application's Git version
  information to be displayed in the backend footer.

- Replace cryptacular with bcrypt for password hashing as cryptacular causes
  issues

- Upgrade colander, python-gnupg, requests and SQLAlchemy

- Move PDFLaTeX templates to presentation layer

- Fix issue to make invoices always available from backend. They had not been
  available from backend after a defined period of time. This behavior is
  intended for email links but not for backend.



1.27.1
======


- Use Python 2 for now

- Fix first general assembly creation

- Freeze required modules due to incompatibilities

- Introduce view processing. View processing provides functionality for pre-
  and post-processing especially to validate and transform view input like URL
  pattern matchdict, GET and POST.

- Refactor general assembly invitations to use view processing validation

- Refactor membership certificate to use view processing validation

- Refactor membership acquisition to use validation and proper integration
  tests. Membership acquisition is refactored to use view processing
  validation. At the same time integration tests for membership acquisition are
  rebuilt from scratch introducing a general base for integration testing.

- Refactor member detail to use validation and proper integration tests. Member
  detail is refactored to use view processing validation. At the same time
  integration tests for member detail are rebuilt from scratch introducing a
  general base for integration testing.

- Cleanup code

- Introduce caching to footer version information

- Start cleaning up personal data schema. There were three declarations of very
  similar Colander schemas for personal data including name and address. These
  three can be unified to reduce redundant code and improve test coverage.



1.27
====


- Introduce dues invoice repository to the data layer.

- Show membership numbers instead of IDs after batch dues invoice sending and
  batch general assembly invitation sending.

- General assembly 2019 invitations.



1.26
====


- Move general assembly invitations to a separate table for a clean and
  normalised data model.

- Send invitations form general assembly detail page.

- Show member details page after member general assembly invitation.

- Add general assembly creation.

- Add general assembly editing.

- Add dues 2019.

- Let payments and reductions depend on whether there is an invoice instead of
  the type of membership.



1.25
====


- Introduce configuration value for status email recipient.

  - The previously existing configuation option c3smembership.mailaddr is
    renamed to c3smembership.notification_sender. The notification sender email
    address is used for sending emails like the email address confirmation
    link, the membership certificate and dues invoices.

  - The status receiver email address option c3smembership.status_receiver is
    used as a recipient for status emails send by the membership application
    like the new application email which informs the staff that a new
    application was submitted.

- Update GnuPG key. This must still be moved to configuration!

- Show member details in tabs.

- Display membership loss date as date picker instead of text field.

- Show member delete button only if membership has not been accepted.

- Start generalising general assembly invitations.



1.24.1
======


- Fix email sender.

- Fix dues reduction.



1.24
====


- Migrate frontend to new design.

- Cleanup templates and view and move them to the presentation layer.

- Cleanup data model and move it to data layer.

- Simplify pagination page size change.



1.23.1
======


- Restrict dues invoice access. Dues invoices can only be downloaded if they
  have not been paid yet and only for one year.

- Use email address from settings instead of hard-coded.

- Unify descriptions and field names for signature and payment reception date.



1.23
====


Migrate backend to new design.



1.22
====


- Add date filtering to payment list.

- Copy the logic for the 2017 dues invoices for 2018 as a dirty quick fix. The
  whole dues and invoicing logic still needs a complete redesign to make it
  reusable for any year, any type of invoice and any type of accounting.



1.21
====


- Fix double entry when applicant edits details.

- Remove membership type handling: During the crowdfunding campaign C3S got
  members of which the information was not complete. It was unknown whether
  they were natural persons or legal entities and whether they were full or
  investing members. The functionality to determine the membership type
  including sending emails and handling responses is no longer needed and
  therefore removed.

- Fix email address confirmation email sending from backend.

- Add membership type column to dashboard and membership list.

- Add membership loss to annual reporting.

- Adjust privacy statement checkbox text

- Move privacy statement link to footer

- Add privacy statement to application form PDF

- Fix accountant application email duplication. The email notification to the
  accountant was sent each when the applicant loaded the application PDF. This
  resulted in the accountant getting another email if the PDF was reloaded
  later on. Not the email is sent after the applicant confirmed their form data
  and thereby submitted.

- Add payment list to toolbox. The list so far contains all membership dues
  payments and is primarily intended for bookkeeping validation.



1.20.7
======


Fix membership list showing entities who lost membership before.



1.20.6
======


Add mandatory data privacy statement consent to registration form.



1.20.5
======


- Remove editing of number of shares hold by a member.

- Remove old import and export functionality.

- Show error message if applicant is younger than 18 years old.

- Invitations for general assembly and bar camp 2018.

- Hide invoice 2017 sending in membership list and toolbox.



1.20.4
======


Update signatures of the managing directors.



1.20.3
======


Update names of the managing directors.



1.20.2
======


Add an explicit section to the membership form describing that the C3S statute
and membership dues regulations determine periodic payments.



1.20.1
======


Add sentence in membership application form to clarify notice period and
membership fee (possibly required due to legal change).



1.20
====


- Make the invoice URL independent of the email address as it can change but
  keep backward compatibility for 2015 and 2016.

- Don't send invoices from batch if membership was lost.

- Don't show invoice button in membership list when invoice cannot be sent.

- Fix invoice note for owing balance from previous years.

- Only display invoice information and send invoices if entity hold membership
  during the respective year.

- Disable membership list button for 2017 general assembly and barcamp
  invitations.

- Copy the logic for the 2016 dues invoices for 2017 as a dirty quick fix. The
  whole dues and invoicing logic still needs a complete redesign to make it
  reusable for any year, any type of invoice and any type of accounting.



1.19.2
======


- Changed name of chairperson of the board of directors in email footer.

- Pin Python package SQLAlchemy to version 1.0.9 due to issues with 1.1.5.

- Fix statistics to correctly count and show lost memberships.



1.19.1
======


Minor fixes in email templates for general assembly and bar camp 2017.



1.19
====


- Invitations for general assembly and bar camp 2017.

- Deactivate invoice sending for 2016 in membership list and toolbox.



1.18.1
======


Fix data type issues by treating date values as date and not datetime.



1.18
====


- Fix template syntax issues.

- Fix statistics translation issue.

- Send emails from yes@c3s.cc instead of yes@office.c3s.cc.

- Add functionality to toolbox to get membership list PDFs for specific dates
  and end of years.

- Membership certificate must not be generated once a member lost membership.

  - Prevent certificate email sending

  - Prevent PDF generation from email link and backend

  - Do not show certificate section in membership details

  - Do not show certificate links in backend membership list

- Membership lists must not show entities which lost membership.

- Remove outdated database fixes.

- Move common data model classes to the data layer.

- Document architectural patterns.

- Remove additional shares purchasers list.

- Remove old code which was only used once

  - Import founders

  - Import crowdfunders

  - Fix crowdfunders import

  - Make founders, yessers and crowdfunders members

  - Flag duplicates

  - Merge duplicates



1.17.2
======


- Renew GnuPG key. This must really be moved to configuration!



1.17.1
======


- Include LaTeX package gensymb into membership list template header to render
  the degree control sequence.

- Remove birthday from pdf membership list.

- Remove "mbH" (limited liability company) from membership list header.



1.17
====


- Copy the logic for the 2015 dues invoices for 2016 as a dirty quick fix. The
  whole dues and invoicing logic needs a complete redesign to make it reusable
  for any year, any type of invoice and any type of accounting.

- Disable buttons in membership list for sending general assembly and barcamp
  invitations.



1.16.1
======


- Use TeX escaping for dues invoice generation.



1.16
====


- Introduce architectural layers and start moving the implementation
  accordingly:

  - The presentation layer contains all user interface specific implementation.
    This includes all Pyramid specific logic. Presentation uses the business
    layer for retrieving information and processing it.

  - The business layer contains als business logic which is independent from the
    the logic on how to store the data or how to present it. Business uses the
    data layer for retrieving data and storing it.

  - The data layer's purpose is to retrieve and store data and provide an
    abstract interface which is independent of the underlying storage system.

- Move schemas to separate presentation layer package. Schemas are used to
  validate user input. They are therefore part of the presentation layer.

- Introduce a reusable pagination mechanism to present paged data.

- Add separate template for membership certificate emails to legal entities.

- Remove dashboard_only.

- Reorganise internationalisation. The internationalisation should be part of
  the presentation layer and moved there in a future release.

- Rename header template block from 'css'to 'head'.

- Add navigation buttons to the dues invoices listing.

- Membership dues

  - Fix issue with invoice generation for members without proper membership type.

  - Fix issue that invoices for dues 2015 were created for members approved in 2016.

  - Add invoice archiving batch process.



1.15.1
======


- Fix handling of None/NULL for email_invite_flag_bcgv16.

- Membership dues: Disable batch invoicing in toolbox.



1.15
====


- Update more executive directors. (This must be moved to configuration!)

- Cleanup email templating.

- Add links for sending payment and signature confirmation emails to details
  page.

- Include submission date into membership application notification email.

- Let make member function return to page of origin, either dashboard or
  details page.

- Personalise emails which are sent from the application to members.

- Adjustments for barcamp and general assembly 2016.



1.14
====


- Extend requirements specification and documentation of business processes.

- Extend documentation about production deployment of new application
  versions.

- Fix tests.

- Cleanup ci.sh. Manual copying of TextInputSliderWidget is not necessary
  anymore since 1.12-beta.

- Handle loss of membership including resignation, expulsion, death,
  bankrupsy, winding-up and transfer of remaining shares.



1.13.1
======


- Fix URL for corporation membership application form.

- Extend documentation about production deployment of new application
  versions.

- Handle loss of membership including resignation, expulsion, death,
  bankruptcy and transfer of remaining shares.

- Introduce tex tools for escaping special characters.



1.13
====


- Update executive director. (This must be moved to configuration!)

- Add progress bar to membership application process.

- Improve usability of membership application process.

- Fix C3S Statute reference to use the version independent URL.

- Fix German Cultural Commons Manifesto link and title.

- Extend requirements specification and documentation of business processes.



1.12
====


- Fix minor issues with application form templates.



1.12-beta.4
===========


- Extend monthly membership invoice statistics by current balance.

- Fix backend membership certificate url.



1.12-beta.3
===========


- Fix singular/plural phrasing issue in shares payment confirmation email
  text.

- Extend monthly membership invoice statistics by paid amounts.



1.12-beta.2
===========


- Documentation: Fix git push command for pushing the version tag, 'origin'
  was missing.

- Add reference to membership dues regulations to membership application.

- Fix issue with certificate generation from backend member details page.



1.12-beta
=========


- Include version information into dashboard view and template. Create
  helper class GitTools to provide git information about tags, branches and
  commits.

- Code cleanup

  - accountants_view.py

  - views.py

- Integrate the deform TextInputSliderWidget so that it doesn't need
  to be applied as a text and neither the slider.pt template needs to
  be copied anywhere. This reduces manual setup steps to run the
  application.

- Change salutation of payment reminder email body.

- Fix several German typos like "Nachnahme" instead of "Nachname", "Email"
  instead of "E-Mail" and "Addresse" instead of "Adresse".

- Change certificate email templates from .pt to .txt as they are plain
  text, therefore not compatible with .pt internationalization and causing
  parsing errors.

- Fix several template HTML syntax errors.

- Fix setup.py which was referencing CHANGES.txt instead of CHANGES.md which
  is now CHANGES.rst.

- Make the link to the Cultural Commons Manifesto language specific in order
  to show the C3S website in the corresponding language.

- Fix several internationalization issues with the membership application
  formular.

- Documentation:

  - Use version number from python package.

  - Document development branching model.

  - Document internationalization of template and python files.

  - Provide documentation with the running app at /docs

- Extend statistics for a monthly summary of membership invoices.

- Registration form:

  - Add acknowledgement checkbox and links for membership dues regulations.

  - Add password confirmation field.

  - Mark password field on validation error and remind the user to re-enter
    it.

- Fix minor issues of the membership application form:

  - Old name "C3S SCE i.G." was used in German form.

  - Bottom images were not exported to PDF.



1.11.2
======


- Fix permissions for reversal invoice generation as users cannot access it.



1.11.1
======

- Fix notation of euro values and currency symbols.

- Remove unnecessary empty lines at beginning and end of email texts.

- Workaround for German character "ß" (sharp s) in LaTeX documents.

- Clarify phrasing in English membership dues emails.



1.11
====


- Introduce membership dues handling. Dues are calculated per quarter
  depending on the membership duration.

  - Invoices are generated and sent to the member. They can be canceled.

  - Membership dues can be reduced which leads to a canceling of the previous
    invoice and generation of a new one.

  - The payment can be entered with amount and date.

- Extend documentation.

  - An overview of the application is given.

  - The source code documentation auto-generated.

  - How to run the test.

  - Setup for development is descibed.

  - How to deploy the application onto an Apache server is explained.

- Invitation emails for the 2015 general assembly and barcamp.

- Cleanup code.

- Fixed minor bugs.



1.10.2
======


- Fix jQuery path in dashboard template which was preventing the
  confirmation dialog for deleting a member to be shown. Made sure that
  a wrong jQuery path would not allow deletions without confirmation dialog
  in the future.

- Fix usage of jQuery, jQuery UI and Bootstrap. Reorganized files and
  corrected all references.

- Fix link to statistics of finished memberships.

- Set GPL license for c3sMembership code and CC BY 4.0 for documentation.

- Add copyright notice for c3sMembership code and documentation as well
  as redistributed works.

- Add license texts GPL and MIT for redistributed works.

- Add license texts section to documentation.

- Add list of contributors.

- Implemente redirect for member deletion based on route name.



1.10.1
======


- Remove column "BC/GV" from Application for Membership dashboard. Emails
  were sent without confirmation when clicking the button.

- Introduce version number to c3sMembership. Start with 1.10.1. The
  application has been productively used for some time (i.e. at least 1.0)
  and went through a few changes since then. Therefore, taking 1.10.0 for
  the existing version 1.10.0 seems reasonable.
