import pytest
from rdflib import Namespace, ConjunctiveGraph
from topica.models import Item, Tag, Cluster

TOPICA = Namespace('http://example.com/topica/')


@pytest.mark.django_db
def test_linkages_between_clusters():
    graph = ConjunctiveGraph()
    graph.parse(format='trig', data="""
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix topica: <http://example.com/topica/> .
    @prefix dbpedia: <http://dbpedia.org/resource/> .

    dbpedia:Scotland {
        dbpedia:Scotland topica:tag dbpedia:Robert_Burns, dbpedia:United_Kingdom .

        dbpedia:Robert_Burns rdfs:label "Robert Burns" .
        dbpedia:United_Kingdom rdfs:label "United Kingdom" .
    }

    dbpedia:England {
        dbpedia:England topica:tag dbpedia:William_Shakespeare, dbpedia:United_Kingdom .

        dbpedia:William_Shakespeare rdfs:label "William Shakespeare" .
        dbpedia:United_Kingdom rdfs:label "United Kingdom" .
    }

    dbpedia:Goat {
        dbpedia:Goat topica:tag dbpedia:Horns, dbpedia:Milk .

        dbpedia:Horns rdfs:label "Horns" .
        dbpedia:Milk rdfs:label "Milk" .
    }
    """)
    from rdflib_django import utils

    utils.get_conjunctive_graph().parse(data=graph.serialize(format='nquads'),
                                        format='nquads')

    cluster_scotland = Cluster()
    cluster_scotland.save()
    cluster_england = Cluster()
    cluster_england.save()
    cluster_goat = Cluster()
    cluster_goat.save()

    Item(iri='http://dbpedia.org/resource/Scotland',
         cluster=cluster_scotland).save()
    Item(iri='http://dbpedia.org/resource/England',
         cluster=cluster_england).save()
    Item(iri='http://dbpedia.org/resource/Goat', cluster=cluster_goat).save()

    assert cluster_scotland.linkage(cluster_scotland) == 0.0
    assert cluster_england.linkage(cluster_england) == 0.0
    assert cluster_goat.linkage(cluster_goat) == 0.0
    # Scotland is more like England than it is to a goat
    assert cluster_scotland.linkage(cluster_england) < cluster_scotland.linkage(
        cluster_goat)

    # cheeky second test to prove the agglomeration because I'm too lazy to
    # break out all the setup above into a fixture just yet
    Cluster.agglomerate()

    assert Cluster.objects.all().count() == 2
    assert cluster_goat.item_set.count() == 1
    assert Item.get_or_create(
        iri='http://dbpedia.org/resource/Scotland').cluster == Item.get_or_create(
        iri='http://dbpedia.org/resource/England').cluster


@pytest.mark.django_db
def test_cluster_cohesion_is_one_when_items_are_identical():
    graph = ConjunctiveGraph()
    graph.parse(format='trig', data="""
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix topica: <http://example.com/topica/> .
    @prefix dbpedia: <http://dbpedia.org/resource/> .

    dbpedia:Scotland {
        dbpedia:Scotland topica:tag dbpedia:Robert_Burns, dbpedia:United_Kingdom .

        dbpedia:Robert_Burns rdfs:label "Robert Burns" .
        dbpedia:United_Kingdom rdfs:label "United Kingdom" .
    }

    dbpedia:Alba {
        dbpedia:Alba topica:tag dbpedia:Robert_Burns, dbpedia:United_Kingdom .

        dbpedia:Robert_Burns rdfs:label "Robert Burns" .
        dbpedia:United_Kingdom rdfs:label "United Kingdom" .
    }

    """)
    from rdflib_django import utils

    utils.get_conjunctive_graph().parse(data=graph.serialize(format='nquads'),
                                        format='nquads')

    cluster = Cluster()
    cluster.save()

    Item(iri='http://dbpedia.org/resource/Scotland',
         cluster=cluster).save()
    Item(iri='http://dbpedia.org/resource/Alba',
         cluster=cluster).save()

    assert cluster.cohesion() == 1.0

@pytest.mark.django_db
def test_cluster_cohesion_is_zero_when_items_are_fully_unrelated():
    graph = ConjunctiveGraph()
    graph.parse(format='trig', data="""
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix topica: <http://example.com/topica/> .
    @prefix dbpedia: <http://dbpedia.org/resource/> .

    dbpedia:Scotland {
        dbpedia:Scotland topica:tag dbpedia:Robert_Burns, dbpedia:United_Kingdom .

        dbpedia:Robert_Burns rdfs:label "Robert Burns" .
        dbpedia:United_Kingdom rdfs:label "United Kingdom" .
    }

    dbpedia:Goat {
        dbpedia:Goat topica:tag dbpedia:Horns, dbpedia:Milk .

        dbpedia:Horns rdfs:label "Horns" .
        dbpedia:Milk rdfs:label "Milk" .
    }

    """)
    from rdflib_django import utils

    utils.get_conjunctive_graph().parse(data=graph.serialize(format='nquads'),
                                        format='nquads')

    cluster = Cluster()
    cluster.save()

    Item(iri='http://dbpedia.org/resource/Scotland', cluster=cluster).save()
    Item(iri='http://dbpedia.org/resource/Goat', cluster=cluster).save()

    assert cluster.cohesion() == 0.0

@pytest.mark.django_db
def test_cluster_cohesion_is_between_zero_and_one_when_items_overlaps():
    graph = ConjunctiveGraph()
    graph.parse(format='trig', data="""
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix topica: <http://example.com/topica/> .
    @prefix dbpedia: <http://dbpedia.org/resource/> .

    dbpedia:Scotland {
        dbpedia:Scotland topica:tag dbpedia:Robert_Burns, dbpedia:United_Kingdom .

        dbpedia:Robert_Burns rdfs:label "Robert Burns" .
        dbpedia:United_Kingdom rdfs:label "United Kingdom" .
    }

    dbpedia:England {
        dbpedia:England topica:tag dbpedia:William_Shakespeare, dbpedia:United_Kingdom .

        dbpedia:William_Shakespeare rdfs:label "William Shakespeare" .
        dbpedia:United_Kingdom rdfs:label "United Kingdom" .
    }

    """)
    from rdflib_django import utils

    utils.get_conjunctive_graph().parse(data=graph.serialize(format='nquads'),
                                        format='nquads')

    cluster = Cluster()
    cluster.save()

    Item(iri='http://dbpedia.org/resource/Scotland',
         cluster=cluster).save()
    Item(iri='http://dbpedia.org/resource/England',
         cluster=cluster).save()

    assert round(cluster.cohesion(), 2) == 0.33
