#! /bin/bash

pytest -x -v \
    --cov-report term-missing \
    --cov-report html:cov.html \
    --cov-report xml:cov.xml \
    --junitxml junit.xml \
    --cov c3smembership c3smembership/
