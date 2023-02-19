Docker Setup for c3sMembership
==============================


Services
--------

+---------------+-------------------------+-----------------+-------------+
| Service       | Description             | Profiles        | Ports       |
+===============+=========================+=================+=============+
| server        | Pyramid App             | | production    | 80: http    |
|               |                         | | staging       |             |
|               |                         | | development   |             |
+---------------+-------------------------+-----------------+-------------+
| mail          | Mailhog Test Mailserver | development     | 8025: http  |
+---------------+-------------------------+-----------------+-------------+
| tests         | Pyramid App             | testing         |             |
+---------------+-------------------------+-----------------+-------------+
| browser       | Selenium Chrome Browser | testing         |             |
+---------------+-------------------------+-----------------+-------------+
| documentation | Sphinx Build Service    | documentation   |             |
+---------------+-------------------------+-----------------+-------------+


Files
-----

    .
    ├── .env.example            # environment variables
    ├── compose.yaml            # service definitions for docker containers
    ├── Dockerfile              # build instructions for docker images
    │
    ├── docker-entrypoint.sh    # entrypoint for docker commands
    ├── docker_development.ini  # pyramid config file for docker environment
    ├── requirements.sh         # sorts pip requirements by application context
    │
    └── DOCKER.rst              # this readme


Dependencies
------------

- `docker`_

.. _docker: https://docs.docker.com/engine/install/


Install
-------

Clone repository:

    git clone https://github.com/c3s/c3sMembership
    cd c3sMembership

Configure git user name/email/signing (optional):

    git config user.name "<NAME>"
    git config user.email "<EMAIL>"
    git config user.signingkey "<GPGKEYID>"
    git config commit.gpgsign true

Configure `/etc/hosts` (optional):

    127.0.0.1   yes.test

Copy and configure `.env` example file:

    cp .env.example .env
    xdg-open .env

    UID=<UID_OF_YOUR_USER>
    GID=<GID_OF_YOUR_USER>

Build docker images:

    COMPOSE_PROFILES=development,testing,documentation docker compose build

Initialize database:

    docker compose run --rm server initialize_c3sMembership_db development.ini


Run
---

Run all docker services and attach to the logs:

    docker compose up

Run a one-shot command on a new container and remove the container afterwards:

    docker compose run --rm <SERVICE> <COMMAND>
    docker compose run --rm server ls

Run a command on a running container:

    docker compose exec <SERVICE> <COMMAND>
    docker compose exec server ls

Open a bash on a container:

    docker compose [run --rm|exec] server bash

Stop all services:

    docker compose down --remove-orphans


Develop
-------

Open web interface:

    xdg-open yes.test

Open mailhog:

    xdg-open yes.test:8025

Run tests:

    docker compose run --rm tests

Run tests multiple times from within the container:

    docker compose run --rm tests bash
    > pytest -v -x

Run specific tests verbose, cancel on first error:

    docker compose run --rm tests \
        pytest -v -x c3smembership/tests/test_initialization.py -k test_main_correct

    docker compose run --rm tests bash
    > pytests -v -x c3smembership/tests/test_initialization.py -k test_main_correct --pdb

Inspect screenshots of selenium tests:

    ls screenshots

Build docs:

    docker compose run --rm documentation
    xdg-open docs/_build/html/index.html

Backup database:

    cp c3sMembership.db c3sMembership.db.$(date "+%Y-%m-%d_%H-%M-%S")

Migrate database:

    docker compose [run --rm|exec] server alembic upgrade head

Delete database:

    sudo rm c3sMembership.db

Rebuild docker images:

    COMPOSE_PROFILES=development,testing,documentation docker compose build [--no-cache]

