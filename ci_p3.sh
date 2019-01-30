#!/usr/bin/env sh

set -e
#
# continuous integration shell script to set up the project and run tests
#
echo "so you have cloned git@github.com:C3S/c3sMembership.git..."
#
#
# apt-get install python-virtualenv
# sudo apt-get install libxml2-dev libxslt1-dev (needed for pyquery)
# create a virtualenv, preferrably with the python 2.7 variant:
virtualenv -p python3 env3
# update setuptools if neccessary
env3/bin/pip install --upgrade pip
env3/bin/pip install -U setuptools
# set it up
# this will take a little while and install all necessary dependencies.
env3/bin/python setup.py develop
# delete the old database, if it exists
if [ -f c3sMembership.db ]; then
    rm c3sMembership.db
fi
# populate the database
env3/bin/initialize_c3sMembership_db development.ini
# prepare for tests
env3/bin/pip install nose coverage pep8 pylint pyflakes pyquery
#
# test preparation
#
#
# we use selenium for user interface tests. so we need firefox and xvfb
# start Xvfband send it to the background: Xvfb :10 &
export DISPLAY=:10
# run the tests
env3/bin/nosetests c3smembership/   --with-coverage --cover-html --with-xunit
# this is how you can run individial tests:
#env/bin/nosetests c3smembership/tests/test_webtest.py:FunctionalTests.test_faq_template

# for pyflakes
find c3smembership -regex '.*.py' ! -regex '.*tests.*'|egrep -v '^./tests/'|xargs env/bin/pyflakes  > pyflakes.log || :
# for pylint
rm -f pylint.log
for f in `find c3smembership -regex '.*.py' ! -regex '.*tests.*'|egrep -v '^./tests/'`; do
env/bin/pylint --output-format=parseable --reports=y $f >> pylint.log
done || :
