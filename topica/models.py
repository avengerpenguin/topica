import laconia
from httplib2 import iri2uri
from django.db import models
from rdflib_django import utils


class Item(models.Model):

    class Meta:
        app_label = 'topica'

    iri = models.CharField(max_length=255, unique=True)

    def __init__(self, *args, **kwargs):
        super(Item, self).__init__(*args, **kwargs)
        self._graph = utils.get_named_graph(self.iri)
        factory = laconia.ThingFactory(self._graph)
        self._entity = factory(iri2uri(self.iri))

    def __getattr__(self, item):
        if item == 'query':
            raise AttributeError
        vals = set(getattr(self._entity, item))
        return list(vals)

    def set_lang(self, newlang):
        self._entity.lang = newlang

    def get_or_create(cls, iri):
        things = cls.objects.filter(iri=iri)
        if things.count() == 0:
            thing = cls(iri=iri)
            thing.save()
        else:
            thing = things[0]

        return thing
