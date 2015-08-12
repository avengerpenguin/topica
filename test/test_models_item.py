import re
import pytest
import testypie
import httpretty
from rdflib import URIRef, RDF, Literal, Namespace, RDFS, ConjunctiveGraph
from topica.models import Item, Tag


TOPICA = Namespace('http://example.com/topica/')


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

    # When
    item = Item(iri=iri)
    item.save()

    # Then
    assert (URIRef('http://dbpedia.org/resource/Kevin_Bacon'), RDF.type, Literal('Person')) in item.graph


@pytest.mark.django_db
def test_get_single_tag():
    from rdflib_django import utils
    graph = utils.get_named_graph('http://dbpedia.org/resource/Scotland')
    graph.add((URIRef('http://dbpedia.org/resource/Scotland'), TOPICA.tag, URIRef('http://dbpedia.org/resource/Robert_Burns')))
    graph.add((URIRef('http://dbpedia.org/resource/Robert_Burns'), RDFS.label, Literal('Robert Burns')))

    item = Item(iri='http://dbpedia.org/resource/Scotland')
    item.save()

    assert len(item.get_tags()) == 1
    assert Tag('http://dbpedia.org/resource/Robert_Burns', 'Robert Burns') in item.get_tags()


@pytest.mark.django_db
def test_get_many_tags():
    from rdflib_django import utils
    graph = utils.get_named_graph('http://dbpedia.org/resource/Scotland')
    graph.add((URIRef('http://dbpedia.org/resource/Scotland'), TOPICA.tag, URIRef('http://dbpedia.org/resource/Robert_Burns')))
    graph.add((URIRef('http://dbpedia.org/resource/Robert_Burns'), RDFS.label, Literal('Robert Burns')))
    graph.add((URIRef('http://dbpedia.org/resource/Scotland'), TOPICA.tag, URIRef('http://dbpedia.org/resource/William_Wallace')))
    graph.add((URIRef('http://dbpedia.org/resource/William_Wallace'), RDFS.label, Literal('William Wallace')))

    item = Item(iri='http://dbpedia.org/resource/Scotland')
    item.save()

    assert len(item.get_tags()) == 2
    assert Tag('http://dbpedia.org/resource/Robert_Burns', 'Robert Burns') in item.get_tags()
    assert Tag('http://dbpedia.org/resource/William_Wallace', 'William Wallace') in item.get_tags()


@pytest.mark.django_db
def test_distance_between_identical_items_is_zero():
    from rdflib_django import utils
    g1 = utils.get_named_graph('http://dbpedia.org/resource/Scotland')
    g1.add((URIRef('http://dbpedia.org/resource/Scotland'), TOPICA.tag, URIRef('http://dbpedia.org/resource/Robert_Burns')))
    g1.add((URIRef('http://dbpedia.org/resource/Robert_Burns'), RDFS.label, Literal('Robert Burns')))
    g1.add((URIRef('http://dbpedia.org/resource/Scotland'), TOPICA.tag, URIRef('http://dbpedia.org/resource/William_Wallace')))
    g1.add((URIRef('http://dbpedia.org/resource/William_Wallace'), RDFS.label, Literal('William Wallace')))

    g2 = utils.get_named_graph('http://dbpedia.org/resource/Alba')
    g2.add((URIRef('http://dbpedia.org/resource/Alba'), TOPICA.tag, URIRef('http://dbpedia.org/resource/Robert_Burns')))
    g2.add((URIRef('http://dbpedia.org/resource/Robert_Burns'), RDFS.label, Literal('Robert Burns')))
    g2.add((URIRef('http://dbpedia.org/resource/Alba'), TOPICA.tag, URIRef('http://dbpedia.org/resource/William_Wallace')))
    g2.add((URIRef('http://dbpedia.org/resource/William_Wallace'), RDFS.label, Literal('William Wallace')))

    item1 = Item(iri='http://dbpedia.org/resource/Scotland')
    item1.save()
    item2 = Item(iri='http://dbpedia.org/resource/Alba')
    item2.save()

    assert item1.get_distance(item2) == 0.0
    assert item2.get_distance(item1) == 0.0


@pytest.mark.django_db
def test_distance_between_overlapping_items():
    from rdflib_django import utils
    g1 = utils.get_named_graph('http://dbpedia.org/resource/Scotland')
    g1.add((URIRef('http://dbpedia.org/resource/Scotland'), TOPICA.tag, URIRef('http://dbpedia.org/resource/Robert_Burns')))
    g1.add((URIRef('http://dbpedia.org/resource/Robert_Burns'), RDFS.label, Literal('Robert Burns')))
    g1.add((URIRef('http://dbpedia.org/resource/Scotland'), TOPICA.tag, URIRef('http://dbpedia.org/resource/United_Kingdom')))
    g1.add((URIRef('http://dbpedia.org/resource/United_Kingdom'), RDFS.label, Literal('United Kingdom')))

    g2 = utils.get_named_graph('http://dbpedia.org/resource/England')
    g2.add((URIRef('http://dbpedia.org/resource/England'), TOPICA.tag, URIRef('http://dbpedia.org/resource/United_Kingdom')))
    g2.add((URIRef('http://dbpedia.org/resource/United_Kingdom'), RDFS.label, Literal('United Kingdom')))
    g2.add((URIRef('http://dbpedia.org/resource/England'), TOPICA.tag, URIRef('http://dbpedia.org/resource/William_Shakespeare')))
    g2.add((URIRef('http://dbpedia.org/resource/William_Shakespeare'), RDFS.label, Literal('William Shakespeare')))

    item1 = Item(iri='http://dbpedia.org/resource/Scotland')
    item1.save()
    item2 = Item(iri='http://dbpedia.org/resource/England')
    item2.save()

    assert item1.get_distance(item2) == 2.0/3.0
    assert item2.get_distance(item1) == 2.0/3.0


@pytest.mark.django_db
def test_item_created_in_own_cluster():
    item = Item(iri='http://dbpedia.org/resource/Kevin_Bacon')
    item.save()
    assert item.cluster is not None
    assert item.cluster.item_set.count() == 1
