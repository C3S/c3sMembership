from webtest import TestApp

# Prevent pytest from trying to collect webtest's TestApp as tests:
TestApp.__test__ = False
