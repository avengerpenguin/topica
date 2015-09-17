import os
from rdflib import Graph, Namespace, URIRef
from FuXi.Rete.RuleStore import SetupRuleStore
from FuXi.Rete.Util import generateTokenSet
from FuXi.Horn.HornRules import HornFromN3
from .models import Item
import re
from rdflib_django import utils


FOAF = Namespace('http://xmlns.com/foaf/0.1/')


def fetch(iri):
    graph = Graph()
    graph.parse(iri)
    if 'http://www.bbc.co.uk/programmes/' in iri:
        graph.parse(iri + '.rdf')
        graph.add((URIRef(iri), FOAF.primaryTopic, URIRef(iri + '#programme')))
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
    return graph + closure_delta


def enrich(graph):
    tag_iris = [row.iri for row in graph.query(
            """
            PREFIX topica: <http://example.com/topica/>

            SELECT DISTINCT ?iri ?name
            WHERE {
                ?entity topica:tag ?iri .
            }
            """)]
    for iri in tag_iris:
        print 'Including: ' + iri
        graph.parse(iri)
        m = re.match('^(http://www.bbc.co.uk/programmes/.+?)#[a-z]+$', iri)
        if m:
            uri = m.group(1)
            print 'Including: ' + uri + '.rdf'
            graph.parse(uri + '.rdf')
            graph.add((URIRef(uri), FOAF.primaryTopic, URIRef(iri)))
    return graph


def ingest(iri):
    graph = utils.get_named_graph(iri)
    graph.bind('topica', 'http://example.com/topica/')
    graph += enrich(translate(fetch(iri)))

    return Item.get_or_create(iri)
