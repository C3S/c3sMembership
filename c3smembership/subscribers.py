from pyramid.renderers import get_renderer
from pyramid.httpexceptions import HTTPFound


def add_frontend_template(event):
    frontend = get_renderer(
        'presentation/templates/page-base/frontend.pt').implementation()
    event.update({'frontend': frontend})


def add_backend_template(event):
    backend = get_renderer(
        'presentation/templates/page-base/backend.pt').implementation()
    event.update({'backend': backend})


def add_old_backend_template(event):
    old_backend = get_renderer(
        'presentation/templates/page-base/old_backend.pt').implementation()
    event.update({'old_backend': old_backend})


LANGUAGE_MAPPING = {  # a dictionary of codes the browsers send
    'da': 'da',  # # # # and the locales we choose for them
    'de': 'de',  # # # # used in the subscriber below
    'de_AT': 'de',
    'de_CH': 'de',
    'de_DE': 'de',
    'en': 'en',
    'en_CA': 'en',
    'en_GB': 'en',
    'en_US': 'en',
    'es': 'es',
    'fr': 'fr',
    # ... add new languages here, too!
}


def add_locale(event):
    """
    give user a cookie to determine the language to display.
    if user has chosen another language by clicking a flag,
    give her that language (cookie & redirect).
    ask users browser for language to display,
    fallback to english if language is not available.
    """
    # exclude requests
    path = event.request.path
    if path.startswith('/static/') or path.startswith('/_debug_toolbar/'):
        return

    # default locale
    current = 'en'

    # cookie locale
    cookie = event.request.cookies.get('_LOCALE_')
    if cookie:
        current = LANGUAGE_MAPPING.get(cookie, current)

    # check browser for language, if no cookie present
    if not cookie:
        current = event.request.accept_language.best_match(LANGUAGE_MAPPING) \
            or current

    # language request
    request = event.request.params.get('language')  # ?language=<LANG>
    if not request:                                 # ?<LANG>
        params = list(event.request.params)
        if len(params) == 1:
            request = LANGUAGE_MAPPING.get(params[0], None)
    if request:
        current = LANGUAGE_MAPPING.get(request, current)
        event.request.response = HTTPFound(location=event.request.path_url)

    event.request.locale_name = current
    event.request.response.set_cookie('_LOCALE_', value=current)
