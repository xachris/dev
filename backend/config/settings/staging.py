from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403,F401

DEBUG = False

if SECRET_KEY == "unsafe-development-only":  # noqa: F405
    raise ImproperlyConfigured("Staging 必须设置 DJANGO_SECRET_KEY。")
