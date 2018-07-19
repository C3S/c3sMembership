from pyramid.renderers import get_renderer
from pyramid.i18n import (
    default_locale_negotiator,
)


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


BROWSER_LANGUAGES = {  # a dictionary of codes the browsers send
    'da': 'da',  # # # # and the locales we choose for them
    'de': 'de',  # # # # used in the subscriber below
    'de_AT': 'de',
    'de_CH': 'de',
    'de_DE': 'de',
    'en': 'en',
    'en-CA': 'en',
    'en-GB': 'en',
    'en-US': 'en',
    'es': 'es',
    'fr': 'fr',
    # ... add new languages here, too!
}


def add_locale_to_cookie(event):
    """
    give user a cookie to determine the language to display.
    if user has chosen another language by clicking a flag,
    give her that language (cookie & redirect).
    ask users browser for language to display,
    fallback to english if language is not available.
    """
    DEBUG = False

    # if user clicked at particular language flag
    if event.request.query_string is not '':
        # the list of available languages is taken from the .ini file:
        # either development.ini or production.ini
        languages = event.request.registry.settings[
            'available_languages'].split()
        if event.request.query_string in languages:
            # we want to reload the page in this other language
            lang = event.request.query_string

            # so we put it on the request object as locale and redirect info
            event.request._LOCALE_ = event.request._REDIRECT_ = lang
            # and we set a cookie
            event.request.response.set_cookie('_LOCALE_', value=lang)

            if DEBUG:  # pragma: no cover
                print("switching language to " + lang)
            # from pyramid.httpexceptions import HTTPFound
            # print("XXXXXXXXXXXXXXX ==> REDIRECTING in subscriber")
            # return HTTPFound(location=event.request.route_url('intent'),
            #                 headers=event.request.response.headers)
            #
            # redirect not working here!
            # redirects to relevant language,
            # but does not clean URL from query_string in browser
            # redirecting in views.py using _REDIRECT_ attribute of the request

    # get locale from request
    locale = default_locale_negotiator(event.request)

    if DEBUG:  # pragma: no cover
        print("locale (from default_locale_negotiator): " + str(locale))

    # if locale is not already set, look at browser information
    if locale is None and event.request.accept_language:
        # print "request.accept_language: " + str(
        #     event.request.accept_language)
        # print "locale is None but accept_language exists!"
        locale = event.request.accept_language.best_match(BROWSER_LANGUAGES)
        # print "locale aus accept_language:" + locale
        locale = BROWSER_LANGUAGES.get(locale)
        # print "locale aus BROWSER_LANGUAGES:" + str(locale)

    # if we have nothing, assume english as fallback
    if locale is None and not event.request.accept_language:
        # print("locale could not be determined by browsers Accept-Language. "
        #      + "defaulting to English")
        locale = 'en'

    # print "setting locale: " + str(locale)
    # make the request know which language to respond with
    event.request._LOCALE_ = locale
    # store language setting in cookie
    event.request.response.set_cookie('_LOCALE_', value=locale)
