"""
Django settings for ShieldDFL project.

Docs:
- Settings: https://docs.djangoproject.com/en/4.2/ref/settings/
- Static files: https://docs.djangoproject.com/en/4.2/howto/static-files/
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# CORE DJANGO SETTINGS
# ============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-shielddfl-2024-secret-key-change-in-production'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,*',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Application definition
INSTALLED_APPS = [
    # Django default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'corsheaders',
    'django_bootstrap5',

    # Local apps - ShieldDFL
    'accounts',
    'federated_learning',
    'blockchain',
    'reputation',
    'privacy',
    'security',
    'dashboard',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'shielddfl.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',   # Global templates directory
        ],
        'APP_DIRS': True,            # Also load templates from each app/templates
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'shielddfl.wsgi.application'

# ============================================================================
# DATABASE (MySQL)
# ============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='shielddfl_db'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default='root'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# ============================================================================
# AUTH / PASSWORD
# ============================================================================

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

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Login/Logout flow
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:user_dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

# ============================================================================
# INTERNATIONALIZATION
# ============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ============================================================================
# STATIC & MEDIA FILES
# ============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# REST FRAMEWORK
# ============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# ============================================================================
# CORS
# ============================================================================

CORS_ALLOW_ALL_ORIGINS = True  # For dev; tighten in production
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ============================================================================
# SESSION / CSRF
# ============================================================================

SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

CSRF_COOKIE_SECURE = False  # True in HTTPS production
CSRF_COOKIE_HTTPONLY = False

# ============================================================================
# EMAIL (Dev)
# ============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ============================================================================
# SHIELDFL CUSTOM SETTINGS
# ============================================================================

# Federated Learning Settings
FL_SETTINGS = {
    'MIN_DEVICES': config('FL_MIN_DEVICES', default=5, cast=int),
    'MAX_DEVICES': config('FL_MAX_DEVICES', default=50, cast=int),
    'ROUNDS_PER_EPOCH': config('FL_ROUNDS', default=10, cast=int),
    'LOCAL_EPOCHS': 3,
    'LEARNING_RATE': 0.01,
    'BATCH_SIZE': 32,
    'REPUTATION_THRESHOLD': 0.5,
    'AGGREGATION_METHOD': 'FedAvg',
}

# Blockchain Settings
BLOCKCHAIN_SETTINGS = {
    'DIFFICULTY': config('BLOCKCHAIN_DIFFICULTY', default=4, cast=int),
    'MINING_REWARD': 10,
    'CONSENSUS_ALGORITHM': 'HYBRID',  # HYBRID, POW, or POS
    'MIN_REPUTATION_TO_MINE': 0.5,
    'BLOCK_TIME_TARGET': 60,  # seconds
}

# Privacy / Differential Privacy Settings
PRIVACY_SETTINGS = {
    'EPSILON': config('PRIVACY_EPSILON', default=1.0, cast=float),
    'DELTA': config('PRIVACY_DELTA', default=1e-5, cast=float),
    'CLIP_NORM': 1.0,
    'NOISE_MULTIPLIER': 1.1,
    'MAX_GRADIENT_NORM': 1.0,
    'QUERY_EPSILON': 1.0,
    'GRADIENT_EPSILON': 1.0,
}

# Security & Attack Detection
SECURITY_SETTINGS = {
    'SAR_THRESHOLD': 3.5,          # z-score threshold for SAR detection
    'BASR_THRESHOLD': 3.0,         # z-score threshold for BASR detection
    'ANOMALY_DETECTION': True,
    'MALICIOUS_DEVICE_THRESHOLD': 0.2,  # reputation below blocks device
    'AUTO_BLOCK_MALICIOUS': True,
}

# LSTM Reputation Model
REPUTATION_SETTINGS = {
    'LSTM_HIDDEN_SIZE': 32,
    'LSTM_NUM_LAYERS': 2,
    'LSTM_SEQUENCE_LENGTH': 10,
    'LEARNING_RATE': 0.001,
    'DEFAULT_REPUTATION': 0.5,
    'HISTORY_WINDOW': 10,
}

# ============================================================================
# LOGGING
# ============================================================================

LOGGING_DIR = BASE_DIR / 'logs'
LOGGING_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOGGING_DIR / 'shielddfl.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'fl_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOGGING_DIR / 'fl_engine.log',
            'formatter': 'verbose',
        },
        'blockchain_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOGGING_DIR / 'blockchain.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'shielddfl': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'federated_learning': {
            'handlers': ['fl_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'blockchain': {
            'handlers': ['blockchain_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'reputation': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'security': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ============================================================================
# CACHING (simple in-memory cache for dev)
# ============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'shielddfl-cache',
    }
}

# ============================================================================
# OPTIONAL: Celery (commented; you can enable when needed)
# ============================================================================

# CELERY_BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = TIME_ZONE

# ============================================================================
# SECURITY (production hardening – enable when deploying)
# ============================================================================

# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# X_FRAME_OPTIONS = 'DENY'
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# ============================================================================
# ENSURE DIRECTORIES EXIST
# ============================================================================

# Ensure media/static subdirectories exist
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
(MEDIA_ROOT / 'models').mkdir(exist_ok=True)
(MEDIA_ROOT / 'datasets').mkdir(exist_ok=True)
(MEDIA_ROOT / 'logs').mkdir(exist_ok=True)
(MEDIA_ROOT / 'uploads').mkdir(exist_ok=True)
STATIC_ROOT.mkdir(parents=True, exist_ok=True)
