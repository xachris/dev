import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403,F401

DEBUG = False

if SECRET_KEY == "unsafe-development-only":  # noqa: F405
    raise ImproperlyConfigured("Production 必须设置 DJANGO_SECRET_KEY。")

SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
CSRF_TRUSTED_ORIGINS = []
if railway_public_domain:
    CSRF_TRUSTED_ORIGINS.append(f"https://{railway_public_domain}")
