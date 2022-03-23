#!/bin/bash

# check, if the script is executed in a service environment
if [ -z "$ENVIRONMENT" ] || [ -z "$WORKDIR" ]; then
    echo "This script is intended to run within a service container."
    echo "Please do not try to execute it on the host."
    exit 1
fi

# install c3smembership module and set flagfile
if ! [ -f /tmp/.pip_module_c3smembership_installed ]; then
    echo "installing module c3smembership ..."
    pip install -q -e .
    touch /tmp/.pip_module_c3smembership_installed
fi

# run command
exec "$@"
