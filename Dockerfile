ARG ENVIRONMENT=development
ARG WORKDIR=/code
ARG DEBUGGER_DEBUGPY=0


#==============================================================================
# Base Images (Debian)
#==============================================================================

#--- BASE ---------------------------------------------------------------------

### production
FROM debian:bookworm-slim AS base_production
# set workdir
ARG WORKDIR
ENV WORKDIR $WORKDIR
ENV PATH $PATH:$WORKDIR
RUN mkdir -p $WORKDIR
WORKDIR $WORKDIR
# configure apt
ENV DEBIAN_FRONTEND noninteractive
# install base packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        locales \
        ssl-cert \
        ca-certificates \
        libmagic1 \
    && rm -rf /var/lib/apt/lists/*
# configure language
RUN sed -i 's/^# *\(de_DE.UTF-8\)/\1/' /etc/locale.gen; \
    sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen
RUN locale-gen
RUN localedef -i de_DE -f UTF-8 de_DE.UTF-8
ENV LANGUAGE de_DE.UTF-8
ENV LANG de_DE.UTF-8
ENV LC_ALL de_DE.UTF-8

### staging
FROM base_production AS base_staging

### testing
FROM base_staging AS base_testing

### development
FROM base_testing AS base_development
# install development packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    && apt-get install -y --no-install-recommends \
        git \
        htop \
        iputils-ping \
        net-tools \
        vim \
        nano \
    && rm -rf /var/lib/apt/lists/*

### result
FROM base_${ENVIRONMENT} AS base


#--- base -> PYTHON -----------------------------------------------------------

### production
FROM base AS python_production
# install python
RUN apt-get update && apt-get install -y --no-install-recommends \
    && apt-get install -y --no-install-recommends \
        curl \
        python3 \
        python3-venv \
        python3-distutils \
        python3-pip  \
        python-is-python3 \
    && rm -rf /var/lib/apt/lists/*
# create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV VIRTUAL_ENV=/opt/venv
# upgrade essential pip packages
# setuptools<81: https://github.com/Pylons/pyramid/issues/3731
RUN python3 -m pip install --upgrade pip wheel "setuptools<81"

### staging
FROM python_production AS python_staging
ENV PYTHONUNBUFFERED 1

### testing
FROM python_staging AS python_testing

### development
FROM python_testing AS python_development

### result
FROM python_${ENVIRONMENT} AS python


#--- base -> python -> PYRAMID ------------------------------------------------

### production
FROM python AS pyramid_production
# install python
RUN apt-get update && apt-get install -y --no-install-recommends \
    && apt-get install -y --no-install-recommends \
        gpg \
        libxslt1.1 \
        pdftk \
        sqlite3 \
        texlive-latex-base \
        texlive-latex-recommended \
        texlive-latex-extra \
        texlive-fonts-recommended \
        texlive-fonts-extra \
        texlive-pictures \
        texlive-lang-german \
        texlive-luatex \
    && rm -rf /var/lib/apt/lists/*
ARG UID
ARG GID
RUN install -d -o $UID -g $GID /.cache

### staging
FROM pyramid_production AS pyramid_staging

### testing
FROM pyramid_staging AS pyramid_testing

### development
FROM pyramid_testing AS pyramid_development

### result
FROM pyramid_${ENVIRONMENT} AS pyramid


#--- base -> python -> COMPILE ------------------------------------------------

FROM python AS compile
# install libs
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        default-jdk-headless \
        git \
        graphviz \
        python3.11-dev \
        # pip: cffi \
            libffi-dev \
        # pip: lxml \
            libxml2-dev \
            libxslt1-dev \
        # ? \
            zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
RUN curl -L 'http://downloads.sourceforge.net/project/plantuml/plantuml.jar' \
      -o /opt/plantuml.jar


#==============================================================================
# Compilation Images
#==============================================================================

#--- [COMPILE] PYRAMID --------------------------------------------------------

### production
FROM compile AS pyramid_production_compiled
COPY requirements_production.txt /requirements_production.txt
RUN pip install --use-pep517 -r /requirements_production.txt

### staging
FROM pyramid_production_compiled AS pyramid_staging_compiled
COPY requirements_staging.txt /requirements_staging.txt
RUN pip install --use-pep517 -r /requirements_staging.txt

### testing
FROM pyramid_staging_compiled AS pyramid_testing_compiled
COPY requirements_testing.txt /requirements_testing.txt
RUN pip install --use-pep517 -r /requirements_testing.txt

### development
FROM pyramid_testing_compiled AS pyramid_development_compiled
COPY requirements_development.txt /requirements_development.txt
RUN pip install --use-pep517 -r /requirements_development.txt

### result
FROM pyramid_${ENVIRONMENT}_compiled AS pyramid_compiled


#==============================================================================
# Service Images
#==============================================================================

#--- base -> python -> pyramid -> SERVER --------------------------------------

FROM pyramid AS server
ARG UID
ARG GID
COPY --chown=${UID}:${GID} --from=pyramid_compiled /opt/venv /opt/venv
# optionally install the Claude Code CLI for in-container, AI-assisted
# debugging. Enabled by setting AI_USECLAUDE=1 in .env (build arg). The CLI runs
# as the non-root ${UID} user (required for yolo mode); the API key is passed at
# runtime via the ANTHROPIC_API_KEY environment variable (see compose.yaml).
ARG AI_USECLAUDE=0
ENV CLAUDE_CONFIG_DIR=/opt/claude
RUN if [ "$AI_USECLAUDE" = "1" ]; then \
        export NODE_OPTIONS=--dns-result-order=ipv4first \
        && echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4 \
        && curl -4 -fsSL https://deb.nodesource.com/setup_20.x | bash - \
        && apt-get install -y --no-install-recommends nodejs \
        && rm -rf /var/lib/apt/lists/* /etc/apt/apt.conf.d/99force-ipv4 \
        && npm install -g @anthropic-ai/claude-code \
        && install -d -o "$UID" -g "$GID" "$CLAUDE_CONFIG_DIR" ; \
    fi

#--- base -> python -> compile -> DOCS ----------------------------------------

FROM compile AS documentation
ARG UID
ARG GID
COPY --chown=${UID}:${GID} --from=pyramid_compiled /opt/venv /opt/venv

