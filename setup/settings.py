
"""
Django settings for setup project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-$t_)%n6sl9g-v9vgziw4dtw)s9$^1)s)obu)fy!m)(fyrkkky*'

DEBUG = True

ALLOWED_HOSTS = ['172.20.10.14', '172.16.192.165', '127.0.0.1', 'localhost']
                                                                                                                                                                                                                                                                                                        
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes', 
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gestao',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'setup.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 
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

WSGI_APPLICATION = 'setup.wsgi.application'


# --- BASE DE DADOS (CORRIGIDA COM TIMEOUT) ---

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,  # Resolve o erro "database is locked"
        },
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator' },
]


# Internationalization
LANGUAGE_CODE = 'pt-pt'
TIME_ZONE = 'Europe/Lisbon'
USE_I18N = True
USE_TZ = True


# --- CONFIGURAÇÃO DE FICHEIROS ESTÁTICOS E MEDIA ---

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",          
    BASE_DIR / "gestao" / "static", 
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'


# --- CONFIGURAÇÃO DE EMAIL (GMAIL SMTP) ---

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Credenciais de autenticação
EMAIL_HOST_USER = 'rodrigo.fmoura04@gmail.com' 
EMAIL_HOST_PASSWORD = 'xtuoqqpaoahjlqla'  # A tua senha de app gerada

# Remetente padrão (Ajustado para o teu e-mail real para evitar rejeição)
DEFAULT_FROM_EMAIL = 'Oficina MESH <rodrigo.fmoura04@gmail.com>'


# --- SEGURANÇA E REDIRECIONAMENTOS ---

# Confiança para as origens de acesso (Adicionados os teus IPs locais)
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8001', 
    'http://localhost:8001',
    'http://172.20.10.14:8001',
    'http://172.16.192.165:8001'
]

LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'dashboard' 
LOGIN_URL = '/admin/login/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'