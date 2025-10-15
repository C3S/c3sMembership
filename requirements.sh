#!/bin/bash
#
# splits requirements into environments using a list of top-level dependencies:
#
#   - requirements.txt
#   - requirements_production.txt
#   - requirements_staging.txt
#   - requirements_testing.txt
#   - requirements_development.txt
#
# find out top-level dependencies:
#
#   $ pip install pipdeptree
#   $ pipdeptree --warn silence | grep -E '^\w+'

# define top level packages
PRODUCTION=(
    alembic
    bcrypt
    colorama
    cornice
    deform
    fdfgen
    lingua
    pbkdf2
    pycountry
    pyramid-beaker
    pyramid-chameleon
    pyramid-mailer
    pyramid-tm
    python-gnupg
    requests
    zope.sqlalchemy
)
STAGING=()
TESTING=(
    coverage
    docutils
    mock
    pytest
    pytest-cov
    pylint
    flake8
    pyquery
    selenium
    sphinx
    sphinxcontrib-plantuml
    waitress
    WebTest
)
DEVELOPMENT=(
    pdbpp
    pyramid-debugtoolbar
    debugpy
)
EXCLUDE=(
    c3smembership
    pip
    pipdeptree
    setuptools
    wheel
)

# install pipdeptree
pip -q install pipdeptree

# production
[ $PRODUCTION ] && \
    pipdeptree --exclude "$(IFS=, ; echo "${EXCLUDE[*]:--}")" \
               --freeze --packages "$(IFS=, ; echo "${PRODUCTION[*]:--}")" \
    > requirements_production.txt

# staging
echo "-r requirements_production.txt" > requirements_staging.txt
[ $STAGING ] && \
    pipdeptree --exclude $(IFS=, ; echo "${EXCLUDE[*]:--}") \
               --freeze --packages $(IFS=, ; echo "${STAGING[*]:--}") \
    >> requirements_staging.txt

# testing
echo "-r requirements_production.txt" > requirements_testing.txt
echo "-r requirements_staging.txt" >> requirements_testing.txt
[ $TESTING ] && \
    pipdeptree --exclude $(IFS=, ; echo "${EXCLUDE[*]:--}") \
               --freeze --packages $(IFS=, ; echo "${TESTING[*]:--}") \
    >> requirements_testing.txt

# development
echo "-r requirements_production.txt" > requirements_development.txt
echo "-r requirements_staging.txt" >> requirements_development.txt
echo "-r requirements_testing.txt" >> requirements_development.txt
[ $DEVELOPMENT ] && \
    pipdeptree --exclude $(IFS=, ; echo "${EXCLUDE[*]:--}") \
               --freeze --packages $(IFS=, ; echo "${DEVELOPMENT[*]:--}") \
    >> requirements_development.txt

