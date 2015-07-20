import os
from rdflib import Graph
from rdflib_django import utils
from FuXi.Rete.RuleStore import SetupRuleStore
from FuXi.Rete.Util import generateTokenSet
from FuXi.Horn.HornRules import HornFromN3
from .models import Item


def fetch(iri):
    graph = Graph()
    graph.parse(iri)
    return graph


def translate(graph):
    rule_store, rule_graph, network = SetupRuleStore(makeNetwork=True)
    rules = HornFromN3(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'rules.n3'))
    closure_delta = Graph()
    network.inferredFacts = closure_delta
    for rule in rules:
        network.buildNetworkFromClause(rule)

    network.feedFactsToAdd(generateTokenSet(graph))
    return closure_delta


def enrich(graph):
    return graph


def ingest(iri):
    graph = utils.get_named_graph(iri)
    graph.bind('topica', 'http://example.com/topica/')
    graph += enrich(translate(fetch(iri)))
    Item.get_or_create(iri)
