#!/bin/bash

echo "extracting message strings..."
env/bin/python setup.py extract_messages
echo "updating po files..."
env/bin/python setup.py update_catalog
echo "edit with POEDIT or transifex <-- TODO!"
# TODO :-)
echo "compiling catalog (POEDIT does this anyways)"
env/bin/python setup.py compile_catalog
touch c3smembership/__init__.py
echo "Pyramid should restart if stared with --reload. Otherwise restart \
manually to see the internationalization's effects."
