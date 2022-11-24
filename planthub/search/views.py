from django.http import JsonResponse
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch
from rest_framework.views import APIView

from .models import PlantHubSearch, PlantHubSpeciesIndex, PlantHubVariableIndex

# Server: config via docker compose
# Local temp: docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node"
#                       docker.elastic.co/elasticsearch/elasticsearch:7.5.2


class Elasticsearch(APIView):
    @staticmethod
    def get(request):

        filter_terms = {}
        filter_terms['genus'] = request.query_params.get("genus")
        filter_terms['family'] = request.query_params.get("family")
        filter_terms['text'] = request.query_params.get("search_term")
        filter_terms['order'] = request.query_params.get("order")
        filter_terms['superorder'] = request.query_params.get("superorder")
        filter_terms['subclass'] = request.query_params.get("subclass")
        filter_terms['class1'] = request.query_params.get("class1")
        filter_terms['species'] = request.query_params.get("species")
        filter_terms['subspecies'] = request.query_params.get("subspecies")
        filter_terms['variable'] = request.query_params.get("variable")

        print(filter_terms)

        ws = PlantHubSearch(filter_terms)
        # count = ws.count()  # Total count of result -> response = ws[0:count].execute() return all hits
        response = ws[0].execute()  # default size is 10 -> set size 0 to return only facets, but not hits

        # todo add observation count to response
        # print("aggreagtion", response.aggregations.Observation_count_by_dataset.__dict__)
        # print("aggreagtion",
        # response.aggregations.Observation_count_by_variable.Observation_count_by_variable2.__dict__)

        finalJSON = {'hits': [], 'facets': []}

        hits = []
        facets = dict()
        list_order = dict()

        list_order['title'] = 1
        list_order["species"] = 2
        list_order["subspecies"] = 2
        list_order["genus"] = 3
        list_order["family"] = 4
        list_order["order"] = 5
        list_order["superorder"] = 6
        list_order["subclass"] = 7
        list_order["class1"] = 8
        list_order["variable"] = 5
        list_order["variable_type"] = 6

        facets_ordered = []

        for facet in response.facets:
            for (facet_, count, selected) in response.facets[facet]:
                # print(facet_)
                if len(str(facet_)) > 0:
                    if facet not in facets:
                        facets[facet] = []
                        facets[facet] = [{'name': facet_, 'count': count}]
                        facets_ordered.append({'name': facet, 'order': list_order[facet]})
                    else:
                        facets[facet].append({'name': facet_, 'count': count})

        finalJSON['hits'] = hits
        finalJSON['facets'] = facets
        finalJSON['facets_ordered'] = facets_ordered

        return JsonResponse(finalJSON)


class ElasticsearchSuggest(APIView):
    def get(self, request):
        print(PlantHubSpeciesIndex._index.get_mapping())
        print(PlantHubVariableIndex._index.get_mapping())

        s1 = Search(index='planthub_datasets_index')
        s2 = Search(index='planthub_species_index')
        s3 = Search(index='planthub_variables_index')

        search_term = request.query_params.get("search_term")

        context = ['family', 'genus']

        s1 = s1.suggest('simple_suggestion11', search_term,
                        completion={'field': 'title.completion', 'size': 100})

        s2 = s2.suggest('simple_suggestion21', search_term,
                        completion={'field': 'taxon_name', 'size': 100, "contexts": {"taxon_rank": context}})

        s2 = s2.suggest('simple_suggestion22', search_term,
                        completion={'field': 'translation.name.completion', 'size': 100})

        s3 = s3.suggest('simple_suggestion31', search_term,
                        completion={'field': 'variable_name.completion', 'size': 100})

        response1 = s1.execute()
        response2 = s2.execute()
        # response3 = s3.execute()

        result = []

        for suggest in response1.suggest.simple_suggestion11[0].options:
            print(suggest.__dict__)
            result.append({'name': suggest._source.title,
                           'cat': 'dataset',
                           'id': suggest._source.title})

        for suggest in response2.suggest.simple_suggestion21[0].options:
            print(suggest.__dict__)
            result.append({'name': suggest._source.taxon_name,
                           'cat': suggest._source.taxon_rank,
                           'id': suggest._source.taxon_name})

        for suggest in response2.suggest.simple_suggestion22[0].options:
            print(suggest.__dict__)
            result.append({'name': suggest._source.name + " (" + suggest._source.lang + ")",
                           'cat': suggest._source.taxon_rank,
                           'id': suggest._source.taxon_name})

        # for suggest in response3.suggest.simple_suggestion31[0].options:
        #     print(suggest.__dict__)
        #     result.append({'name': suggest._source.variable_name,
        #                    'cat': 'variable',
        #                    'id': suggest._source.variable_name.replace(" ", "_")})

        finalJSON = result
        return JsonResponse(finalJSON, safe=False)


class ElasticsearchMatch(APIView):
    def get(self, request):
        # es = Elasticsearch()
        # print(PlantHubIndex._index.get_mapping())

        # m = Mapping.from_es('planthub_species_index', using=es)
        # print(m)
        s = Search()
        search_term = request.query_params.get("search_term")
        # s = s.suggest('simple_suggestion', search_term, term={'field': 'variable_name'})
        #   s = s.suggest('simple_suggestion_2', search_term, completion={'field': 'genus.translation.name.completion'})
        # response = s.execute()
        hits = []
        #  print(response.suggest.simple_suggestion)
        #  print(response.suggest.simple_suggestion_2)
        s = PlantHubVariableIndex.search()

        s.query = MultiMatch(
            query=search_term,
            type="bool_prefix",
            fields=[
                "title",
                "title._2gram",
                "title._3gram",
                "genus.translation.name",
                "genus.translation.name._2gram",
                "genus.translation.name._3gram",
                "variable_name",
                "variable_name._2gram",
                "variable_name._3gram",
            ]
        )

        response = s.execute()

        for hit in response:
            print(hit.__dict__)
            if hit.meta.index == "planthub_variables_index":
                hits.append({'score': round(hit.meta.score, 3),
                             'name': hit.variable_name, 'cat': "variable", 'id': hit.variable_name.replace(" ", "_")})

        finalJSON = hits
        return JsonResponse(finalJSON, safe=False)


class ElasticsearchItem(APIView):
    def get(self, request):

        # Example: http://127.0.0.1:8000/search/index_item?species_index_id=Paeonia
        finalJSON = {'error': "not correct parameter given"}

        if request.query_params.get("species_index_id"):
            species_index_id = request.query_params.get("species_index_id")
            item = PlantHubSpeciesIndex.get(id=species_index_id, ignore=404)
            if item:
                translation = []
                for value in item.translation:
                    translation.append({'name': value.name, 'lang': value.lang})

                finalJSON = {'index_id': species_index_id,
                             'data': {'taxon_name': item.taxon_name,
                                      'taxon_rank': item.taxon_rank, 'translation': translation}}
                return JsonResponse(finalJSON, safe=False)
            else:
                return JsonResponse({'index_id': species_index_id, 'data': 'no found'},
                                    safe=False, status=404)  # not found

        # Example: http://127.0.0.1:8000/search/index_item?variable_index_id=Year
        # todo Adjust after Variable index change
        if request.query_params.get("variable_index_id"):
            variable_index_id = request.query_params.get("variable_index_id")
            item = PlantHubVariableIndex.get(id=variable_index_id, ignore=404)
            if item:
                translation = []
                for value in item.translation:
                    translation.append({'name': value.name, 'lang': value.lang})

                finalJSON = {'index_id': variable_index_id,
                             'data': {'variable_name': item.variable_name,
                                      'variable_description': item.variable_description,
                                      'variable_type': item.variable_type,
                                      'variable_subtype': item.variable_subtype,
                                      'translation': translation}}
                return JsonResponse(finalJSON, safe=False)
            else:
                return JsonResponse({'index_id': variable_index_id, 'data': 'no found'},
                                    safe=False, status=404)  # not found

        return JsonResponse(finalJSON, safe=False, status=412)  # Precondition failed
