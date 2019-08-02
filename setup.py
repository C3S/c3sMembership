"""
Set up the c3sMembership application
"""

import os
import sys

from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.rst')).read()
VERSION = open(os.path.join(HERE, 'VERSION')).read()

REQUIRES = [
    'alembic==0.8.10',  # database schema migration
    'Babel',
    'bcrypt',
    'colander>=1.7.0',
    'cornice==0.17',
    'deform>=2.0.7',  # HTML forms
    'fdfgen==0.11.0',
    'lingua==1.5',  # stick to 1.5 for now. TODO: learn to use 2.1/2.3
    'requests>=2.20.0',
    'pycountry',  # replacing 'webhelpers',
    'pyramid>=1.7',
    'pyramid_beaker',
    'pyramid_chameleon',
    'pyramid_debugtoolbar',
    'pyramid_mailer==0.14.1',
    'pyramid_tm',
    'python-gnupg>=0.4.4',
    'repoze.sendmail==4.1',  # pin to 4.1 because of repoze/repoze.sendmail#31
    # see https://github.com/repoze/repoze.sendmail/issues/31
    'SQLAlchemy>=1.3.0',  # Object-relational mapper
    'transaction',
    'unicodecsv==0.9.4',
    'venusian==1.0',
    'waitress==0.8.9',
    'zope.sqlalchemy>=1.1',
    # webob>=1.8.3 is a pyramid 1.10.4 dependency and for some reason is not
    # installed automatically with pyramid 1.10.4 by pip.
    'webob>=1.8.3',
]
# for the translations machinery using transifex you also need to
# "pip install transifex-client"
TEST_REQUIREMENTS = [
    'coverage',
    'nose',
    'pdfminer',  # and its dependency
    'mock',  # for creating mock objects
    'pylint',
    'pyquery',
    'selenium==3.14.1',  # 4.0.0a1 causes issues by not finding elements
    'slate',  # pdf to text helper
    'webtest',
]

DOCS_REQUIRE = [
    'sphinx==1.3.3',  # for generating the documentation
    'sphinxcontrib-plantuml',
]

if sys.version_info[:3] < (2, 5, 0):
    REQUIRES.append('pysqlite')

setup(
    name='c3smembership',
    version=VERSION,
    description='Membership Form for C3S (form, PDF, email)',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='Christoph Scheid',
    author_email='christoph@c3s.cc',
    url='https://yes.c3s.cc',
    keywords='web wsgi bfg pylons pyramid',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='c3smembership',
    install_requires=REQUIRES + TEST_REQUIREMENTS + DOCS_REQUIRE,
    entry_points="""\
        [paste.app_factory]
        main = c3smembership:main
        [console_scripts]
        initialize_c3sMembership_db = c3smembership.scripts.initialize_db:main
    """,
    # http://opkode.com/media/blog/
    #        using-extract_messages-in-your-python-egg-with-a-src-directory
    message_extractors={
        'c3smembership': [
            ('**.py', 'lingua_python', None),
            ('**.pt', 'lingua_xml', None),
        ]
    },
)
