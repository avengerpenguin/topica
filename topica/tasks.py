import os
import re

from celery import shared_task
from FuXi.Horn.HornRules import HornFromN3
from FuXi.Rete.RuleStore import SetupRuleStore
from FuXi.Rete.Util import generateTokenSet
from rdflib import Graph, Namespace, URIRef
from rdflib_django import utils

from .models import Item

FOAF = Namespace("http://xmlns.com/foaf/0.1/")
TOPICA = Namespace("http://example.com/topica/")


def fetch(iri):
    print(f"Fetching {iri} to create initial graph.")
    graph = Graph(identifier=iri)
    graph.parse(iri)
    if "http://www.bbc.co.uk/programmes/" in iri:
        graph.parse(iri + ".rdf")
        graph.add((URIRef(iri), FOAF.primaryTopic, URIRef(iri + "#programme")))
    print(f"Created graph of length {len(graph)} for entity {iri}")
    return graph


def translate(graph):
    rule_store, rule_graph, network = SetupRuleStore(makeNetwork=True)
    rules = HornFromN3(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "rules.n3")
    )
    closure_delta = Graph()
    network.inferredFacts = closure_delta
    for rule in rules:
        network.buildNetworkFromClause(rule)

    network.feedFactsToAdd(generateTokenSet(graph))
    print(
        f"Inferred {len(closure_delta)} facts for {graph.identifier}"
    )
    return graph + closure_delta


def enrich(graph):
    tag_iris = [
        row.iri
        for row in graph.query(
            """
            PREFIX topica: <http://example.com/topica/>

            SELECT DISTINCT ?iri ?name
            WHERE {
                ?entity topica:tag ?iri .
            }
            """
        )
    ]
    for iri in tag_iris:
        print(f"Adding data for {iri} to graph for {graph.identifier}")
        graph.parse(iri)
        m = re.match("^(http://www.bbc.co.uk/programmes/.+?)#[a-z]+$", iri)
        if m:
            uri = m.group(1)
            print(
                "Adding data for {} to graph for {}".format(
                    uri + ".rdf", graph.identifier
                )
            )
            graph.parse(uri + ".rdf")
            graph.add((URIRef(uri), FOAF.primaryTopic, URIRef(iri)))
    return graph


@shared_task
def ingest(iri):
    graph = utils.get_named_graph(iri)
    graph.bind("topica", "http://example.com/topica/")
    graph += enrich(translate(fetch(iri)))

    return Item.get_or_create(iri)
