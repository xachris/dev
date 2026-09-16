from .base import *  # noqa: F403,F401

DEBUG = False
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
