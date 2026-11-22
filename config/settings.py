from pathlib import Path
import environ
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
env.read_env(BASE_DIR / ".env")

# Keep deployment secrets in the environment, not in source control.
SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-local-development-only-change-before-deploy",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1", ".up.railway.app"],
)

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=["https://*.up.railway.app"],
)

# The OpenAI Python SDK is used with this OpenAI-compatible DeepSeek endpoint.
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
OPENAI_BASE_URL = env(
    "OPENAI_BASE_URL",
    default="https://api.deepseek.com",
)
OPENAI_RECEIPT_MODEL = env(
    "OPENAI_RECEIPT_MODEL",
    default="deepseek-flash",
)
OPENAI_CHAT_MODEL = env(
    "OPENAI_CHAT_MODEL",
    default=OPENAI_RECEIPT_MODEL,
)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'account',
    'clubs',
    'finance',
    'storages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

database_url = env("DATABASE_URL", default="")

if database_url:
    DATABASES = {
        "default": env.db("DATABASE_URL"),
    }
    DATABASES["default"]["CONN_MAX_AGE"] = 600
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kuala_Lumpur'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "account.User"
LOGIN_URL = 'login'


EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=10)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)


USE_CLOUD_STORAGE = env.bool("USE_CLOUD_STORAGE", default=False)

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

if USE_CLOUD_STORAGE:
    storage_values = {
        "access_key": env("AWS_ACCESS_KEY_ID", default=""),
        "secret_key": env("AWS_SECRET_ACCESS_KEY", default=""),
        "endpoint_url": env("AWS_ENDPOINT_URL_S3", default=""),
        "region_name": env("AWS_REGION", default=""),
        "bucket_name": env("AWS_STORAGE_BUCKET_NAME", default=""),
    }

    missing_values = [
        name for name, value in storage_values.items()
        if not value
    ]

    if missing_values:
        raise ImproperlyConfigured(
            "Cloud storage is enabled, but storage settings are missing: "
            + ", ".join(missing_values)
        )

    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            **storage_values,
            "addressing_style": "path",
            "querystring_auth": True,
            "file_overwrite": False,
        },
    }
else:
    STORAGES["default"] = {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    }
