import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-votre-cle-secrete-ici'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

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
LOGIN_REDIRECT_URL = '/'
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
# CONFIGURATION EMAIL SMTP (Ex: Gmail)
# ==========================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# Remplacez ceci par votre VRAIE adresse Gmail
EMAIL_HOST_USER = 'dominiquetiktok8@gmail.com' 
# Remplacez ceci par le "Mot de passe d'application" (16 lettres, sans espaces) généré sur votre compte Google
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'votre-mot-de-passe-d-application')
DEFAULT_FROM_EMAIL = 'G-Parc <dominiquetiktok8@gmail.com>'

# CONFIGURATION GOOGLE OAUTH
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        # Mettre votre vrai client_id et secret fournis par Google Cloud console.
        'APP': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID', 'votre-client-id'),
            'secret': os.environ.get('GOOGLE_CLIENT_SECRET', 'votre-secret'),
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
