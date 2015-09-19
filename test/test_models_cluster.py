import pytest
from rdflib import Namespace, ConjunctiveGraph
from topica.models import Item, Tag, Cluster

TOPICA = Namespace('http://example.com/topica/')


def ingest_graph(graph):
    from rdflib_django import utils
    utils.get_conjunctive_graph().parse(data=graph.serialize(format='nquads'),
                                        format='nquads')

def item_from_graph(graph_path, ident):
    graph = ConjunctiveGraph()
    with open(graph_path) as graph_file:
        graph.parse(format='trig', data=graph_file.read())
    from rdflib_django import utils
    utils.get_conjunctive_graph().parse(data=graph.serialize(format='nquads'),
                                        format='nquads')
    item = Item(iri='http://dbpedia.org/resource/' + ident)
    item.save()
    return item


@pytest.fixture
def scotland():
    return item_from_graph('test/fixtures/scotland.n3', 'Scotland')


@pytest.fixture
def alba():
    return item_from_graph('test/fixtures/alba.n3', 'Alba')


@pytest.fixture
def england():
    return item_from_graph('test/fixtures/england.n3', 'England')


@pytest.fixture
def goat():
    return item_from_graph('test/fixtures/goat.n3', 'Goat')


@pytest.mark.django_db
def test_linkages_between_clusters(scotland, england, goat):

    for item in [scotland, england, goat]:
        assert item.cluster.linkage(item.cluster) == 0.0

    assert scotland.cluster.linkage(england.cluster) < scotland.cluster.linkage(goat.cluster)


@pytest.mark.django_db
def test_agglomerate_merges_two_nearest_clusters(scotland, england, goat):

    # Given we have 3 singleton clusters at the start
    assert Cluster.objects.all().count() == 3

    Cluster.agglomerate()
    # Django will have cached these, so refresh to see latest memberships
    scotland.refresh_from_db()
    england.refresh_from_db()
    goat.refresh_from_db()

    # we should have lost a cluster
    assert Cluster.objects.all().count() == 2
    # Check the goat is still in its own singleton cluster
    assert goat.cluster.item_set.count() == 1
    # England and Scotland should have been merged
    assert scotland.cluster == england.cluster


@pytest.mark.django_db
def test_cluster_cohesion_is_one_when_items_are_identical(scotland, alba):
    cluster = Cluster()
    cluster.save()

    scotland.cluster = cluster
    alba.cluster = cluster

    assert cluster.cohesion == 1.0

@pytest.mark.django_db
def test_cluster_cohesion_is_zero_when_items_are_fully_unrelated(scotland, goat):
    cluster = Cluster()
    cluster.save()

    scotland.cluster = cluster
    scotland.save()
    goat.cluster = cluster
    goat.save()

    assert cluster.cohesion == 0.0


@pytest.mark.django_db
def test_cluster_cohesion_is_between_zero_and_one_when_items_overlaps(scotland, england):
    cluster = Cluster()
    cluster.save()

    scotland.cluster = cluster
    scotland.save()
    england.cluster = cluster
    england.save()

    # Hard-coded to test for the particular method in use, but theoretically
    # the test should probably just check that it's strictly between 0 and 1.
    assert round(cluster.cohesion, 2) == 0.33


@pytest.mark.django_db
def test_cluster_division_separates_cluster_with_unrelated_items(scotland, alba, england, goat):
    cluster_scotland = Cluster()
    cluster_scotland.save()
    cluster_england_and_goat = Cluster()
    cluster_england_and_goat.save()

    scotland.cluster = cluster_scotland
    scotland.save()
    alba.cluster = cluster_scotland
    alba.save()
    england.cluster = cluster_england_and_goat
    england.save()
    goat.cluster = cluster_england_and_goat
    goat.save()

    Cluster.clear_empty()

    assert Cluster.objects.count() == 2

    Cluster.divide()
    # Django won't notice the clusters changing unless we re-read fields
    scotland.refresh_from_db()
    england.refresh_from_db()
    goat.refresh_from_db()

    # We expect one cluster to divide, so our original 2 are now 3
    assert Cluster.objects.count() == 3
    # Scotland cluster untouched as it has two identical items
    assert len(cluster_scotland) == 2
    # England and Goat should be in their own clusters as they are unrelated
    assert england.cluster != goat.cluster
