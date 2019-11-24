.. _sec_deployment:

=================
Deployment (prod)
=================

The basic setup of c3sMembership goes along the lines
presented in :ref:`setup_and_requirements`, so read that first.

For deployment, we use Apache2 with mod_wsgi.
::

   apt-get install apache2 libapache2-mod-wsgi


There are two more things needed:

- Apache VirtualHost Configuration: as normal, but referencing a ..
- WSGI Python File: helps apache to load the app WSGI-style, using the virtualenv.

For the wsgi file, there is an example :download:`here <./yes.wsgi>`.

We assume you know how to set up an Apache VirtualHost configuration file.
These lines can help you to make it use the wsgi file:
::

    # # mod_wsgi approach
    # #
    # # adapted: http://pyramid.readthedocs.org/en/latest/tutorials/modwsgi/index.html
    # # Use only 1 Python sub-interpreter.  Multiple sub-interpreters
    # # play badly with C extensions.

    WSGIApplicationGroup %{GLOBAL}
    WSGIPassAuthorization On
    WSGIDaemonProcess yesc3s user=christoph group=christoph threads=4 python-path=/foo/c3sMembership/env/lib/python2.7/site-packages
    WSGIScriptAlias / /foo/c3sMembership/yes.wsgi

    <Directory /foo/c3sMembership/>
      WSGIProcessGroup yesc3s
      #     WSGIApplicationGroup %{GLOBAL}
      Order allow,deny
      Allow from all
      # new and important for apache 2.4
      Require all granted
    </Directory>


Of course, you should run the production instance behind SSL.

Also review the settings in *production.ini*.
