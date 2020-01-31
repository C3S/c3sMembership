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
    'Babel',  # Internationalization for XML page templates and Python files
    'bcrypt',  # Password hashing. TODO: Use bcrypt instead?
    'colander>=1.7.0',  # Schema validation
    'cornice==0.17',  # API tools
    'deform>=2.0.7',  # HTML forms from colander schemas
    'fdfgen==0.11.0',  # Filling PDF forms
    # Stick to lingua 1.5 for now. TODO: learn to use 2.1/2.3
    'lingua==1.5',  # Internationalization
    'pyramid>=1.7',  # Web framework
    'pyramid_beaker',  # Create a Pyramid session factory from settings
    'pyramid_chameleon',  # Templating for Chameleon page templates
    'pyramid_debugtoolbar',  # Developer debug toolbar
    'pyramid_mailer==0.14.1',  # Send emails
    # Pyramid transaction management, used for development
    'pyramid_tm>=2.2.1',
    'python-gnupg>=0.4.4',  # GPG encryption
    'SQLAlchemy>=1.3.0',  # Object-relational mapper
    # Transaction management, e.g. for database transactions
    'transaction>=2.4.0',
    'unicodecsv==0.9.4',  # Create CSV file
    'zope.sqlalchemy>=1.2',  # TODO: Can it be replaced by SQLAlchemy?
]
# for the translations machinery using transifex you also need to
# "pip install transifex-client"
TEST_REQUIREMENTS = [
    'coverage',  # Get code test coverage for nose
    'mock',  # Creating mock objects for unit testing
    'nose',  # Execute unit testing
    'pylint==1.9.5',  # Code linting
    'pyquery',  # HTML element querying
    'selenium==3.14.1',  # 4.0.0a1 causes issues by not finding elements
    'webtest',  # Run web applications for unit testing

    # Dependency compatibility
    # waitress is required by webtest but version 1.3.0 causes issues
    'waitress==0.8.9',
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
