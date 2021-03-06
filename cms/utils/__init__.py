# -*- coding: utf-8 -*-
# TODO: this is just stuff from utils.py - should be splitted / moved
from cms import constants
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_default_language, get_language_list, get_language_code
from django.conf import settings
from django.core.files.storage import get_storage_class
from django.utils.functional import LazyObject
import os


def get_template_from_request(request, obj=None, no_current_page=False):
    """
    Gets a valid template from different sources or falls back to the default
    template.
    """
    template = None
    if len(get_cms_setting('TEMPLATES')) == 1:
        return get_cms_setting('TEMPLATES')[0][0]
    if "template" in request.REQUEST:
        template = request.REQUEST['template']
    if not template and obj is not None:
        template = obj.get_template()
    if not template and not no_current_page and hasattr(request, "current_page"):
        current_page = request.current_page
        if hasattr(current_page, "get_template"):
            template = current_page.get_template()
    if template is not None and template in dict(get_cms_setting('TEMPLATES')).keys():
        if template == constants.TEMPLATE_INHERITANCE_MAGIC and obj:
            # Happens on admin's request when changing the template for a page
            # to "inherit".
            return obj.get_template()
        return template    
    return get_cms_setting('TEMPLATES')[0][0]


def get_language_from_request(request, current_page=None):
    """
    Return the most obvious language according the request
    """
    language = request.REQUEST.get('language', None)
    site_id = current_page.site_id if current_page else None
    if language:
        language = get_language_code(language)
        if not language in get_language_list(site_id):
            language = None
    if language is None:
        language = get_language_code(getattr(request, 'LANGUAGE_CODE', None))
    if language:
        if not language in get_language_list(site_id):
            language = None

    if language is None and current_page:
        # in last resort, get the first language available in the page
        languages = current_page.get_languages()

        if len(languages) > 0:
            language = languages[0]

    if language is None:
        # language must be defined in CMS_LANGUAGES, so check first if there
        # is any language with LANGUAGE_CODE, otherwise try to split it and find
        # best match
        language = get_default_language(site_id=site_id)

    return language


def get_page_from_request(request):
    from warnings import warn
    from cms.utils.page_resolver import get_page_from_request as new
    warn("'cms.utils.get_page_from_request' is deprecated in favor of "
         "'cms.utils.page_resolver.get_page_from_request' and will be removed "
         "in Django-CMS 2.2.", DeprecationWarning)
    return new(request)


default_storage = 'django.contrib.staticfiles.storage.StaticFilesStorage'


class ConfiguredStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class(getattr(settings, 'STATICFILES_STORAGE', default_storage))()

configured_storage = ConfiguredStorage()

def cms_static_url(path):
    '''
    Helper that prefixes a URL with STATIC_URL and cms
    '''
    if not path:
        return ''
    return configured_storage.url(os.path.join('cms', path))
