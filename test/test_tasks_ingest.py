import re

import httpretty
import pytest
import testypie
from django.db import transaction

from topica.tasks import ingest


@pytest.fixture(autouse=True, scope="module")
def mock_responses(request):
    def callback(http_request, uri, headers):
        httpretty.disable()
        response = testypie.get_response(uri, http_request.headers)
        headers.update(
            {
                key.lower(): value
                for key, value in response["headers"].iteritems()
            }
        )
        print uri
        httpretty.enable()
        return response["code"], headers, response["body"]

    httpretty.enable()
    httpretty.register_uri(httpretty.GET, re.compile(".*"), body=callback)

    request.addfinalizer(httpretty.disable)
    request.addfinalizer(httpretty.reset)


@pytest.mark.django_db
def test_basic_item_creation():
    item = ingest(iri="http://www.bbc.co.uk/programmes/b006t1q9")
    assert item is not None
    assert item.iri == "http://www.bbc.co.uk/programmes/b006t1q9"
    assert len(item.get_tags()) == 2
