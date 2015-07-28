#!/usr/bin/env python

import os
from django.conf import settings
from django.views.generic import TemplateView
import django12factor


# Configuration
BASE_DIR = os.path.dirname(__file__)
d12f = django12factor.factorise()
if not settings.configured:
    settings.configure(
        DEBUG=d12f['DEBUG'],
        TEMPLATE_DEBUG=d12f['TEMPLATE_DEBUG'],
        SECRET_KEY=d12f.get('SECRET_KEY', os.urandom(32)),
        ROOT_URLCONF=__name__,
        MIDDLEWARE_CLASSES=(
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ),
        TEMPLATE_DIRS=(
            os.path.join(BASE_DIR, 'templates'),
        ),
        LOGGING=d12f['LOGGING'],
        DATABASES=d12f['DATABASES'],
        INSTALLED_APPS=(
            'rdflib_django',
            'topica',
        ),
    )


# Views and Routes
from django.conf.urls import url
from django.views.generic import ListView
from . import models

urlpatterns = (
    url(r'^$', ListView.as_view(template_name='home.html', model=models.Cluster, context_object_name='clusters')),
)


from django.core.wsgi import get_wsgi_application


application = get_wsgi_application()
