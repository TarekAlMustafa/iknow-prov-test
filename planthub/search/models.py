from elasticsearch_dsl import (
    Completion,
    Document,
    FacetedSearch,
    Integer,
    Keyword,
    Nested,
    NestedFacet,
    Q,
    SearchAsYouType,
    TermsFacet,
    Text,
    connections,
)

# Connect with es on port
# Todo error handling if not available


connections.create_connection(hosts=['localhost:9200'], timeout=20)


class PlantHubDatasetsIndex(Document):
    title = Text(fielddata=True, fields={'keyword': Keyword(), 'completion': Completion()})
    dataset_id = Integer()
    count = Integer()
    species = Keyword()
    subspecies = Keyword()
    genus = Keyword()
    family = Keyword()
    order = Keyword()
    superorder = Keyword()
    subclass = Keyword()
    class1 = Keyword()

    variables = Nested(
        multi=True,
        properties={
            'name_full': Text(fielddata=True, fields={'keyword': Keyword()}),
            'type': Text(fielddata=True, fields={'keyword': Keyword()}),
            'subtype': Text(fielddata=True, fields={'keyword': Keyword()}),
        }
    )

    class Index:
        name = "planthub_datasets_index"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}


class PlantHubSpeciesIndex(Document):
    taxon_name = Completion(contexts=[{"name": "taxon_rank", "type": "category", "path": "taxon_rank"}])
    taxon_rank = Keyword()
    translation = Nested(
        multi=True,
        properties={
            'name': Text(fielddata=True, fields={'completion': Completion()}),
            'lang': Text(fielddata=True, fields={'keyword': Keyword()}),
            'taxon_name': Keyword(),
            'taxon_rank': Keyword()
        }
    )

    other_keywords = Nested(
        multi=True,
        properties={
            'name': Text(fielddata=True, fields={'keyword': Keyword(), 'completion': Completion()}),
        }
    )

    class Index:
        name = "planthub_species_index"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}


class PlantHubVariableIndex(Document):
    variable_name = Text(fielddata=True, fields={'keyword': Keyword(), 'completion': Completion(),
                                                 'search_as_you_type': SearchAsYouType(max_shingle_size=3)})
    variable_description = Text()
    variable_type = Text(fielddata=True, fields={'keyword': Keyword(), 'completion': Completion()})
    variable_subtype = Text(fielddata=True, fields={'keyword': Keyword(), 'completion': Completion()})

    translation = Nested(
        multi=True,
        properties={
            'name': Text(fielddata=True, fields={'completion': Completion()}),
            'lang': Text(fielddata=True, fields={'keyword': Keyword()}),
            'ref_variable_name': Keyword()
        }
    )

    other_keywords = Nested(
        multi=True,
        properties={
            'name': Text(fielddata=True, fields={'keyword': Keyword(), 'completion': Completion()}),
        }
    )

    class Index:
        name = "planthub_variables_index"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}


class PlantHubSearch(FacetedSearch):
    index = 'planthub_datasets_index'
    doc_types = [PlantHubDatasetsIndex, ]
    fields = ['title^5', 'variables.type', 'variables.name_full']

    facets = {
        'title': TermsFacet(field='title', size=100),
        'species': TermsFacet(field='species', size=100),
        'subspecies': TermsFacet(field='subspecies', size=100),
        'genus': TermsFacet(field='genus', size=100),
        'family': TermsFacet(field='family', size=100),
        'order': TermsFacet(field='order', size=100),
        'superorder': TermsFacet(field='superorder', size=100),
        'subclass': TermsFacet(field='subclass', size=100),
        'class1': TermsFacet(field='class1', size=100),
        'variable': NestedFacet('variables', TermsFacet(field='variables.name_full.keyword', size=300)),
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
        print(self._query["species"])
        if self._query["species"]:
            d = {'species': self._query["species"]}
            search_query = search_query.filter('term', **d)

        if self._query["subspecies"]:
            d = {'subspecies': self._query["subspecies"]}
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

        search_query.aggs.bucket('Observation_count_by_dataset', 'terms', field='title', size=1000)\
            .metric('count_observ', 'sum', field='count')
        search_query.aggs.bucket('Observation_count_by_variable', 'nested', path='variables')\
            .bucket('Observation_count_by_variable2', 'terms', field='variables.name_full', size=1000)\
            .bucket('all_queries', 'reverse_nested').metric('count_observ', 'sum', field='count')
        return search_query
