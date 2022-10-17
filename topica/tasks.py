# -*- coding: utf-8 -*-
from __future__ import print_function
import os
from rdflib import Graph, Namespace, URIRef
from FuXi.Rete.RuleStore import SetupRuleStore
from FuXi.Rete.Util import generateTokenSet
from FuXi.Horn.HornRules import HornFromN3
from .models import Item
import re
from rdflib_django import utils
from celery import shared_task
from SPARQLWrapper import SPARQLWrapper, JSON


FOAF = Namespace('http://xmlns.com/foaf/0.1/')
TOPICA = Namespace('http://example.com/topica/')


def fetch(iri):
    print('Fetching {} to create initial graph.'.format(iri))
    graph = Graph(identifier=iri)
    graph.parse(iri)
    if 'http://www.bbc.co.uk/programmes/' in iri:
        graph.parse(iri + '.rdf')
        graph.add((URIRef(iri), FOAF.primaryTopic, URIRef(iri + '#programme')))


    dbpedia = SPARQLWrapper("http://dbpedia.org/sparql")
    dbpedia.setQuery("""
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            SELECT ?dbpediaEntity
            WHERE {{
                    ?dbpediaEntity dbo:wikiPageExternalLink <{iri}> .
             }}
        """.format(iri=iri))
    dbpedia.setReturnFormat(JSON)
    results = dbpedia.query().convert()
    for result in results["results"]["bindings"]:
        graph.parse(result["dbpediaEntity"]["value"])

    print('Created graph of length {} for entity {}'.format(len(graph), iri))
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
    print('Inferred {} facts for {}'.format(
        len(closure_delta), graph.identifier))
    return graph + closure_delta


def pre_enrich(graph):
    return graph


def post_enrich(graph):
    tag_iris = [row.iri for row in graph.query(
        """
            PREFIX topica: <http://example.com/topica/>

            SELECT DISTINCT ?iri ?name
            WHERE {
                ?entity topica:tag ?iri .
            }
            """)]
    for iri in tag_iris:
        print('Adding data for {} to graph for {}'.format(iri, graph.identifier))
        graph.parse(iri)
        m = re.match('^(http://www.bbc.co.uk/programmes/.+?)#[a-z]+$', iri)
        if m:
            uri = m.group(1)
            print('Adding data for {} to graph for {}'.format(
                uri + '.rdf', graph.identifier))
            graph.parse(uri + '.rdf')
            graph.add((URIRef(uri), FOAF.primaryTopic, URIRef(iri)))
    return graph


@shared_task
def ingest(iri):
    graph = utils.get_named_graph(iri)
    graph.bind('topica', 'http://example.com/topica/')
    graph += post_enrich(translate(pre_enrich(fetch(iri))))

    return Item.get_or_create(iri)
