c3sMembership README
====================
This webapp offers a form to to join *Cultural Commons Collecting Society (C3S)*
as member. A GnuPG encrypted mail with the details submitted will be sent to C3S.

When the form is submitted and the email verified,
form submission data is used to populate a pdf with form fields (using fdf
and pdftk) and the resulting PDF is ready for download.

Another special feature of this app is internationalisation (i18n), making
the form available in several languages. You can help translate this app on
transifex: https://www.transifex.com/projects/p/... tba .../

Help via screencast is available: http://translate.c3s.cc
Also see ./tx/README.rst for more help on the translation machinery.


setup
-----

see ci.sh
install pdftk (sudo apt-get install pdftk)


run (in development mode)
-------------------------

$ pserve development.ini --reload

The app will rebuild templates and reload code whenever there are changes.


run (in production mode, daemon mode)
-------------------------------------

$ pserve production.ini start


Routes and Views for Users
--------------------------

The default route is *'/'* (named 'join'), presenting the join form.
From there, users can follow links to other views with relatively static
information:

* */disclaimer*
* */faq*
* */statute*
* */manifesto*

If the form is used and submitted, after successful validation the
information entered is presented in a view under */success*, where the
user can choose to re-edit (back to the join form) or confirm the data given
and request a validation email by clicking a button. 

At this point (in view */success_check_email*, the data is persisted in a DB
and the session is invalidated, i.e. the app forgets about the users connection.

The user then needs to check her email and come back using the validation link.
The validation link contains the email and a code to identify the user
in view */verify_password*,
where the user additionally has to enter her password.
(Without this password check,
anybody holding the verification link would be able to obtain the users data.)

Givern the code, email and password all match,
a view */success_pdf* presents a link to download the form.


Routes and Views for Accountants
--------------------------------

C3S staff may login to the app at */login* to see the membership applications made
in views */dashboard*, and */detail/{memberid}* especially to get an overview
of and change the relevant status of
- signatures (have we received a valid signature/printed PDF) and
- payment for shares (have we received modey?).

Eventually, there is a */logout* view to log out of that interface.
