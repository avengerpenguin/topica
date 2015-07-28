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

    Cluster.agglomerate()

    assert Cluster.objects.all().count() == 2
    assert cluster_goat.item_set.count() == 1
    assert Item.get_or_create(
        iri='http://dbpedia.org/resource/Scotland').cluster == Item.get_or_create(
        iri='http://dbpedia.org/resource/England').cluster
