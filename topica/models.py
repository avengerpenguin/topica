import itertools
from collections import Counter

from django.db import models
from rdflib import RDFS, Namespace, URIRef
from rdflib_django import utils

TOPICA = Namespace("http://example.com/topica/")


def distance(a, b):
    a_tags = a.get_tags()
    b_tags = b.get_tags()

    union = a_tags.union(b_tags)

    if len(union) == 0:
        return 1.0

    intersection = a_tags.intersection(b_tags)

    return float(len(union) - len(intersection)) / float(len(union))


class Tag(dict):
    def __init__(self, iri, name):
        self["iri"] = iri
        self["name"] = name

    def __hash__(self):
        return hash(self["iri"] + self["name"])


class Item(models.Model):
    iri = models.CharField(max_length=255, unique=True)
    cluster = models.ForeignKey("Cluster")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.graph = utils.get_named_graph(self.iri)

    @classmethod
    def get_or_create(cls, iri):
        things = cls.objects.filter(iri=iri)
        if things.count() == 0:
            thing = cls(iri=iri)
            thing.save()
        else:
            thing = things[0]

        return thing

    @property
    def title(self):
        titles = list(
            self.graph.objects(subject=URIRef(self.iri), predicate=RDFS.label)
        )
        if titles:
            return titles[0]
        else:
            return "UNKNOWN_TITLE"

    def get_tags(self):
        return {
            Tag(name=str(row.name), iri=str(row.iri))
            for row in self.graph.query(
                """
            PREFIX topica: <http://example.com/topica/>

            SELECT DISTINCT ?iri ?name
            WHERE {
                ?entity topica:tag ?iri .
                ?iri    rdfs:label ?name .
            }
            """,
                initBindings={"entity": URIRef(self.iri)},
            )
        }

    def get_distance(self, item):
        return distance(self, item)

    def save(self, *args, **kwargs):
        try:
            self.cluster
        except Cluster.DoesNotExist:
            print(
                "Item {} has no cluster, so placing in its own singleton cluster.".format(
                    self.iri
                )
            )
            cluster = Cluster()
            cluster.save()
            self.cluster = cluster
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or self.iri


class Cluster(models.Model):
    def linkage(self, other_cluster):
        result = max({distance(a, b) for a in self for b in other_cluster})
        return result

    @property
    def cohesion(self):
        n = len(self)
        if n <= 1:
            return 1.0
        return 1.0 - (
            (1.0 / (n ** 2 - n))
            * sum(
                distance(a, b)
                for a, b in itertools.product(self, repeat=2)
                if not a == b
            )
        )

    @classmethod
    def agglomerate(cls):
        two_nearest = sorted(
            (
                (a, b)
                for a in cls.objects.all()
                for b in cls.objects.all()
                if not a == b
            ),
            lambda pair1, pair2: int(
                10 * (pair1[0].linkage(pair1[1]) - pair2[0].linkage(pair2[1]))
            ),
        )[0]

        linkage = two_nearest[0].linkage(two_nearest[1])

        # if linkage > 0.4:
        #     print('Refusing to merge: {} and {} with linkage {}'.format(
        #         two_nearest[0], two_nearest[1], linkage))
        #     return None

        print(
            "Identified two clusters to merge: {} and {} with linkage {}".format(
                two_nearest[0], two_nearest[1], linkage
            )
        )

        for item in two_nearest[1].item_set.all():
            item.cluster = two_nearest[0]
            item.save()

        assert two_nearest[1].item_set.count() == 0
        two_nearest[1].delete()

        return two_nearest[0]

    @classmethod
    def divide(cls):
        """Chooses a cluster that seems to be the most spread out or least
        cohesive then explodes it by putting every item into its own cluster.

        This then relies on the agglomerate() method then re-merging items that
        belong together back into cohesive clusters later on.

        """
        # Which cluster looks the most spread out?
        least_cohesive = sorted(
            (c for c in cls.objects.all()), key=lambda c: c.cohesion
        )[0]

        cohesion = least_cohesive.cohesion

        # if cohesion > 0.7:
        #     print('Refusing to split cluster {} with cohestion {}'.format(least_cohesive, cohesion))
        #     return least_cohesive

        print(
            "Idenfitied cluster to split {} with cohestion {}".format(
                least_cohesive, cohesion
            )
        )

        # Explode the cluster such that each item is now in a singleton cluster
        for item in list(least_cohesive):
            new_cluster = cls()
            new_cluster.save()
            item.cluster = new_cluster
            item.save()

        # Delete the original cluster as it should be empty now
        least_cohesive.delete()

    def top_tags(self):
        return Counter(
            sum((list(item.get_tags()) for item in self), [])
        ).most_common(10)

    @classmethod
    def clear_empty(cls):
        for cluster in cls.objects.all().iterator():
            if len(cluster) == 0:
                print(f"Deleting empty cluster: {cluster}")
                cluster.delete()

    def __str__(self):
        return "cluster-" + str(self.pk) + ": " + str(set(self))

    def __iter__(self):
        return self.item_set.all().iterator()

    def __len__(self):
        return self.item_set.count()

    def __eq__(self, other):
        return type(self) == type(other) and self.pk == other.pk
