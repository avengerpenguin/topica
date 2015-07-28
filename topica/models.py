from django.db import models
from rdflib import URIRef
from rdflib_django import utils


class Tag(dict):
    def __init__(self, iri, name):
        self['iri'] = iri
        self['name'] = name

    def __hash__(self):
        return hash(self['iri'] + self['name'])

class Item(models.Model):
    iri = models.CharField(max_length=255, unique=True)
    cluster = models.ForeignKey('Cluster')

    def __init__(self, *args, **kwargs):
        super(Item, self).__init__(*args, **kwargs)
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

    def get_tags(self):
        return {Tag(name=str(row.name), iri=str(row.iri)) for row in self.graph.query(
            """
            PREFIX topica: <http://example.com/topica/>

            SELECT DISTINCT ?iri ?name
            WHERE {
                ?entity topica:tag ?iri .
                ?iri rdfs:label ?name .
            }
            """, initBindings={'entity': URIRef(self.iri)})}

    def get_distance(self, item):
        my_tags = self.get_tags()
        their_tags = item.get_tags()

        union = my_tags.union(their_tags)
        intersection = my_tags.intersection(their_tags)

        return float(len(union) - len(intersection)) / float(len(union))


    def save(self, *args, **kwargs):
        try:
            self.cluster
        except Cluster.DoesNotExist:
            cluster = Cluster()
            cluster.save()
            self.cluster = cluster
        super(Item, self).save(*args, **kwargs)

    def __str__(self):
        return self.iri


class Cluster(models.Model):
    def linkage(self, cluster):
        return max({a.get_distance(b) for a in self.item_set.all() for b in cluster.item_set.all()})

    @classmethod
    def agglomerate(cls):
        two_nearest = sorted([(a, b)
                              for a in Cluster.objects.all()
                              for b in Cluster.objects.all()
                              if not a == b],
                             lambda pair1, pair2: pair1[0].linkage(pair1[1]) <= pair2[0].linkage(pair2[1])
                             )[0]

        for item in two_nearest[1].item_set.all():
            item.cluster = two_nearest[0]
            item.save()

        assert two_nearest[1].item_set.count() == 0
        two_nearest[1].delete()

    def __str__(self):
        return 'cluster-' + str(self.pk)