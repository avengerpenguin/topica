import re
import pytest
import testypie
import httpretty
from rdflib import URIRef, RDF, Literal
from topica.models import Item


@pytest.fixture(autouse=True, scope='module')
def mock_responses(request):
    def callback(_http_request, uri, headers):
        httpretty.disable()
        response = testypie.get_response(uri, headers)
        httpretty.enable()
        return response['code'], response['headers'], response['body']

    httpretty.enable()
    httpretty.register_uri(httpretty.GET, re.compile('.*'), body=callback)

    request.addfinalizer(httpretty.disable)
    request.addfinalizer(httpretty.reset)


@pytest.mark.django_db
def test_basic_item_creation():
    item = Item(iri='http://dbpedia.org/resource/Kevin_Bacon')
    item.save()
    assert item is not None


@pytest.mark.django_db
def test_can_access_graph_via_item():
    # Given
    iri = 'http://dbpedia.org/resource/Kevin_Bacon'
    from rdflib_django import utils
    graph = utils.get_named_graph(iri)
    graph.add((URIRef('http://dbpedia.org/resource/Kevin_Bacon'), RDF.type, Literal('Person')))

    item = Item(iri=iri)
    item.save()

    assert (URIRef('http://dbpedia.org/resource/Kevin_Bacon'), RDF.type, Literal('Person')) in item.graph
