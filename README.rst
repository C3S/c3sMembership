c3sMembership README
====================

This Pyramid app handles membership for C3S SCE (Cultural Commons Collecting
Society SCE mit beschränkter Haftung).

The app that once started as a form to gain new members has grown to a
membership administration system catering to the needs of a growing European
cooperative (C3S SCE).

Some features:

* Internationalisation (i18n)
* Membership information is persisted in a database.
* GnuPG encrypted mail with details submitted is sent to C3S staff.
* Once the email is verified, form submission data is used to populate a pdf
  with form fields (using fdf and pdftk) and the resulting PDF is ready for
  download.
* Membership certificates (pdflatex)
* Membership dues (pdflatex)


Documentation
-------------

There is plenty of documentation under /docs, both in this repository and in
the running app (if you have sphinx to compile the docs to HTML)::

   cd docs
   make html

A compiled version of the documentation is available at:
https://yes.c3s.cc/docs/


Setup
-----

Install development dependencies::

   $ sudo apt-get install python-pip python-dev python2.7-dev \
      python-virtualenv libxml2-dev libxslt1-dev build-essential \
      pdftk zlib1g-dev phantomjs


Fonts: The .odt files for the membership application in pdftk require the font
Signika which can be downloaded at:
https://www.google.com/fonts/specimen/Signika

Install LaTeX pdf compilation dependencies::

   $ sudo apt-get install texlive-latex-base texlive-latex-recommended \
      texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra pgf \
      texlive-lang-german texlive-luatex

Setup the virtual environment::

   $ virtualenv -p python2 env

Activate the virtual environment and update pip and setuptools::

   $ source env/bin/activate
   $ pip install --upgrade pip setuptools
   $ pip install -r requirements.txt

Install c3sMembership::

   $ python setup.py develop

Install documentation compilation dependencies::

   $ sudo apt-get install graphviz openjdk-7-jre-headless
   $ mkdir utils
   $ wget 'http://downloads.sourceforge.net/project/plantuml/plantuml.jar' \
      -O utils/plantuml.jar
   $ pip install sphinx sphinxcontrib-plantuml

Create an initial database::

   $ initialize_c3sMembership_db development.ini


Run in development mode
-----------------------

Run::

   $ source env/bin/activate
   $ pserve development.ini --reload

The app will rebuild templates and reload code whenever there are changes by
using --reload.


Run in production mode
----------------------

Run::

   $ source env/bin/activate
   $ pserve production.ini start


Running automated tests
-----------------------

Make sure to activate the virtual environment::

   $ source env/bin/activate
   $ nosetests


Database migration
------------------

Migrate database if database model changed (changed models.py?)::

   $ source env/bin/activate
   $ # Backup database
   $ cp c3sMembership.db c3sMembership.db.$(date "+%Y-%m-%d_%H-%M-%S")
   $ # Upgrade database
   $ alembic upgrade head

See https://yes.c3s.cc/docs/development/changes_branches_releases.html#the-production-branch
