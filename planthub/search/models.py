# from elasticsearch import Elasticsearch
from elasticsearch_dsl import FacetedSearch, NestedFacet, Q, TermsFacet, connections

# from elasticsearch import TransportError
from .create_index import PlantHubDatasetsIndex

# Connect with es on port
# Todo error handling if not available


connections.create_connection(hosts=['localhost:9200'], timeout=20)


class PlantHubSearch(FacetedSearch):
    index = 'planthub_datasets_index'
    doc_types = [PlantHubDatasetsIndex, ]
    fields = ['title^5', 'variables.type', 'variables.name_full']

    facets = {
        'title': TermsFacet(field='title', size=100),
        'species': TermsFacet(field='species', size=100),
        'genus': TermsFacet(field='genus', size=100),
        'family': TermsFacet(field='family', size=100),
        'order': TermsFacet(field='order', size=100),
        'superorder': TermsFacet(field='superorder', size=100),
        'subclass': TermsFacet(field='subclass', size=100),
        'class1': TermsFacet(field='class1', size=100),
        'variable': NestedFacet('variables', TermsFacet(field='variables.name_full.keyword', size=100)),
        'variable_type': NestedFacet('variables', TermsFacet(field='variables.type.keyword', size=100)),
    }

    def query(self, search, er):
        q = super(PlantHubSearch, self).search()
        print(self._query)
        # CommentsIndex.search().query('nested', path='user_post_id', query=Q('range', eser_post_id__score={'gt': 42}))
        search_query = q
        # Fuzzy text search within variables type and full name & field list (combined with OR)
        if len(self._query["text"]) > 0:
            search_query = \
                q.query(Q("nested", path="variables",
                          query=Q("multi_match", fields=['variables.type', 'variables.name_full'],
                                  query=self._query["text"], fuzziness="AUTO", operator="AND")) |
                        Q("multi_match", fields=self.fields, query=self._query["text"],
                          fuzziness="AUTO", operator="AND"))

        if self._query["species"]:
            d = {'species': self._query["species"]}
            search_query = search_query.filter('term', **d)

        if self._query["genus"]:
            d = {'genus': self._query["genus"]}
            search_query = search_query.filter('term', **d)

        if self._query["family"]:
            d = {'family': self._query["family"]}
            search_query = search_query.filter('term', **d)

        if self._query["order"]:
            d = {'order': self._query["order"]}
            search_query = search_query.filter('term', **d)

        if self._query["superorder"]:
            d = {'superorder': self._query["superorder"]}
            search_query = search_query.filter('term', **d)

        if self._query["subclass"]:
            d = {'subclass': self._query["subclass"]}
            search_query = search_query.filter('term', **d)

        if self._query["class1"]:
            d = {'class1': self._query["class1"]}
            search_query = search_query.filter('term', **d)

        if (self._query["variable"]):
            d = {'variables.name_full.keyword': self._query["variable"]}
            search_query = search_query.filter(
                'nested', path='variables',
                query=Q(
                    'term', **d
                ))

        return search_query
