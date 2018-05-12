import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()
VERSION = open(os.path.join(here, 'VERSION')).read()

requires = [
    'alembic',  # migrate the database when introducing new fields
    'Babel',
    'colander',
    'cornice',
    'cryptacular',
    'deform',
    'fdfgen',
    'lingua',  # stick to 1.5 for now. TODO: learn to use 2.1/2.3
    'pycountry',  # replacing 'webhelpers',
    'pyramid',  # use pyramid 1.5.2
    'pyramid_beaker',
    'pyramid_chameleon',  # 'pyramid 1.5 extension'
    'pyramid_debugtoolbar',
    'pyramid_mailer', # maybe not the last version to work
    'pyramid_tm',
    'python-gnupg',
    'repoze.sendmail',  # pin to 4.1 because of repoze/repoze.sendmail#31
    # see https://github.com/repoze/repoze.sendmail/issues/31
    'setuptools',
    'SQLAlchemy',
    'transaction',
    'unicodecsv',
    'venusian',
    'waitress',
    'zope.sqlalchemy',
]
# for the translations machinery using transifex you also need to
# "pip install transifex-client"
test_requirements = [
    'coverage',
    'nose',
    #'pdfminer',  # and its dependency
    'mock',  # for creating mock objects
    'pyquery',
    'selenium',
    'setuptools',
    'slate',  # pdf to text helper
    'webtest',
]

docs_require = [
    'sphinx',  # for generating the documentation
    'sphinxcontrib-plantuml',
]

if sys.version_info[:3] < (2, 5, 0):
    requires.append('pysqlite')

setup(name='c3smembership',
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
      install_requires=requires + test_requirements + docs_require,
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
          ]},
      )
