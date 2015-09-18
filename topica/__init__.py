#!/usr/bin/env python
from __future__ import absolute_import
import os
from django.conf import settings
import django12factor
from django.http import HttpResponse
from celery import Celery

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
            #'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ),
        TEMPLATE_DIRS=(
            os.path.join(BASE_DIR, 'templates'),
        ),
        LOGGING=d12f['LOGGING'],
        DATABASES=d12f['DATABASES'],
        INSTALLED_APPS=(
            'rdflib_django',
            'kombu.transport.django',
            'topica',
        ),
    )


# Celery for background tasks
from . import tasks

app = Celery('topica', broker='django://')
app.conf.update(
    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],
)


# Views and Routes
from django.conf.urls import url
from django.views.generic import ListView
from . import models


def ingest(request):
    if request.method == 'POST':
        if request.META.get('CONTENT_TYPE', 'text/uri-list') == 'text/uri-list':

            response = 'OK\n'

            uris = [line.strip() # trim any whitespace
                for line in request.body.decode('utf-8').splitlines()
                if not line.startswith('#')]

            for uri in uris:
                tasks.ingest.delay(uri)
                response += 'Creating item: {}\n'.format(uri)

            return HttpResponse(response, status=201, content_type='text/plain')
        else:
            return HttpResponse(status=415)
    else:
        return HttpResponse(status=405)


urlpatterns = (
    url(r'ingest/?$', ingest),
    url(r'^$', ListView.as_view(template_name='home.html', model=models.Cluster, context_object_name='clusters')),
)


from django.core.wsgi import get_wsgi_application


application = get_wsgi_application()
