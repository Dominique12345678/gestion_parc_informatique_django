import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [
    '1d72-102-64-128-248.ngrok-free.app',
    'localhost',
    '127.0.0.1',
]

# Origines de confiance pour Ngrok (évite les erreurs CSRF)
CSRF_TRUSTED_ORIGINS = [
    'https://1d72-102-64-128-248.ngrok-free.app',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# ==========================================
# APPLICATION DEFINITION
# ==========================================

INSTALLED_APPS = [
    # 1. Unfold (doit être AVANT l'admin natif)
    "unfold",
    "unfold.contrib.filters",  # Optionnel : filtres plus modernes
    "unfold.contrib.forms",    # Optionnel : formulaires améliorés

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 2. Ton application unique
    'core_app',

    # 3. Third party
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

# Modèle Utilisateur Personnalisé
AUTH_USER_MODEL = 'core_app.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Middleware nécessaire pour allauth
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = 'core.urls'

# ==========================================
# TEMPLATES SEGMENTATION
# ==========================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # On dit à Django de chercher dans le dossier /templates à la racine
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.csrf',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ==========================================
# DATABASE (SQLite pour le développement)
# ==========================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==========================================
# AUTHENTICATION & ALLAUTH CONFIG
# ==========================================

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# Configuration allauth pour l'inscription moderne
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory' # Pour ton système de code par mail
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = '/'

# ==========================================
# INTERNATIONALIZATION
# ==========================================

LANGUAGE_CODE = 'fr-fr' # Français

TIME_ZONE = 'Africa/Lome' # Fuseau horaire Togo

USE_I18N = True

USE_TZ = True

# ==========================================
# STATIC AND MEDIA FILES (SÉPARATION PROPRE)
# ==========================================

# Fichiers Statiques (CSS, JS, Images design)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
# STATIC_ROOT = BASE_DIR / 'staticfiles' # Utile uniquement pour la production (Azure/Heroku)

# Fichiers Média (Photos équipements et QR codes)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==========================================
# DEFAULT SETTINGS
# ==========================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================================
# CACHING (Optimisation)
# ==========================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# ==========================================
# CONFIGURATION EMAIL SMTP (Ex: Gmail)
# ==========================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = f"G-Parc <{os.getenv('EMAIL_HOST_USER')}>"

# CONFIGURATION GOOGLE OAUTH
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'secret': os.getenv('GOOGLE_SECRET'),
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}
