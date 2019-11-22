#!/usr/bin/env sh

set -e
#
# continuous integration shell script to set up the project and run tests
#
echo "so you have cloned git@github.com:C3S/c3sMembership.git..."
#
echo "make sure you have *pipenv*, see https://pipenv.readthedocs.io/!"
#
# we try to use pipenv now.
pipenv --version
# if the script fails at this point, you need to install pipenv,
# see https://pipenv.readthedocs.io/en/latest/install/#installing-pipenv
# also read
# https://realpython.com/pipenv-guide/ especially the section
# #i-dont-need-to-distribute-my-code-as-a-package

# sudo apt-get install libxml2-dev libxslt1-dev (needed for pyquery)

pipenv install
#pipenv install -e hg+https://bitbucket.org/dholth/cryptacular@cb96fb3#egg=cryptacular

# set it up
# this will take a little while and install all necessary dependencies.

pipenv run python setup.py develop
#
#
# delete the old database, if it exists
if [ -f c3sMembership.db ]; then
    rm c3sMembership.db
fi
#
# populate the database
pipenv run initialize_c3sMembership_db development.ini
#
# prepare for tests
pipenv install coverage nose mock pep8 pyflakes pylint pyquery selenium webtest
#
# check for pdftk
pdftk --version

# test preparation
#
#
# we use selenium for user interface tests. so we need firefox and xvfb
# start Xvfband send it to the background: Xvfb :10 &
export DISPLAY=:10
# run the tests
pipenv run nosetests c3smembership/   --with-coverage --cover-html --with-xunit
# this is how you can run individial tests:
#pipenv run nosetests c3smembership/tests/test_webtest.py:FunctionalTests.test_faq_template

# for pyflakes
find c3smembership -regex '.*.py' ! -regex '.*tests.*'|egrep -v '^./tests/'|xargs env/bin/pyflakes  > pyflakes.log || :
# for pylint
rm -f pylint.log
for f in `find c3smembership -regex '.*.py' ! -regex '.*tests.*'|egrep -v '^./tests/'`; do
env/bin/pylint --output-format=parseable --reports=y $f >> pylint.log
done || :
