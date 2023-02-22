#!/usr/bin/env sh
#
# continuous integration shell script to set up the project and run tests
#
#
# apt-get install python-virtualenv
# sudo apt-get install libxml2-dev libxslt1-dev (needed for pyquery)
# create a virtualenv, preferrably with the python 2.7 variant:
python -m venv env
# update setuptools if neccessary
env/bin/pip install --upgrade pip
# set it up
# this will take a little while and install all necessary dependencies.
env/bin/pip install -r requirements_testing.txt
env/bin/pip install -q -e .
# delete the old database
rm c3sMembership.db
# populate the database
env/bin/initialize_c3sMembership_db development.ini

# test preparation
#
# we use selenium for user interface tests. so we need firefox and xvfb
# start Xvfband send it to the background: Xvfb :10 &
export DISPLAY=:10
# run the tests
env/bin/pytest -x -v \
    --cov-report term-missing \
    --cov-report html:cov.html \
    --cov-report xml:cov.xml \
    --junitxml junit.xml \
    --cov c3smembership c3smembership/
# this is how you can run individial tests:
#env/bin/nosetests c3smembership/tests/test_webtest.py:FunctionalTests.test_faq_template

# TODO: fix linter errors after py3 upgrade
# for pyflakes
# find c3smembership -regex '.*.py' ! -regex '.*tests.*'|egrep -v '^./tests/'|xargs env/bin/pyflakes  > pyflakes.log || :
# # for pylint
# rm -f pylint.log
# for f in `find c3smembership -regex '.*.py' ! -regex '.*tests.*'|egrep -v '^./tests/'`; do
# env/bin/pylint --output-format=parseable --reports=y $f >> pylint.log
# done || :
