#!/usr/bin/env python

import os, sys
from django.conf import settings
from django.views.generic import TemplateView
import django12factor


# Configuration
BASE_DIR = os.path.dirname(__file__)
d12f = django12factor.factorise()
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
    DATABASES=d12f['DATABASES'],
)


# Views and Routes
from django.conf.urls import url
from django.http import HttpResponse


def index(request):
    return HttpResponse('Hello World')


urlpatterns = (
    url(r'^$', TemplateView.as_view(template_name='home.html')),
)


# Running
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
