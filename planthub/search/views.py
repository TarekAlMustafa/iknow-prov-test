from django.http import JsonResponse
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch
from rest_framework.views import APIView

from .create_index import (
    PlantHubDatasetsIndex,
    PlantHubSpeciesIndex,
    PlantHubVariableIndex,
)
from .models import PlantHubSearch


# Create your views here.
class Elasticsearch(APIView):
    def get(self, request):

        filter = {}
        filter['genus'] = request.query_params.get("genus")
        filter['family'] = request.query_params.get("family")
        filter['text'] = request.query_params.get("search_term")
        filter['order'] = request.query_params.get("order")
        filter['superorder'] = request.query_params.get("superorder")
        filter['species'] = request.query_params.get("species")
        filter['variable'] = request.query_params.get("variable")
        # filter['domain'] =  request.query_params.get("domain")
        print(filter)
        #   print(search_term)
        ws = PlantHubSearch(filter)
        count = ws.count()  # Total count of result)
        response = ws[0:count].execute()  # default size is 10 -> set size to total count

        # print response.__dict__

        finalJSON = {'hits': [], 'facets': []}

        hits = []
        facets = dict()
        list_order = dict()

        # for facet in response.facets:
        #     print facet
        #     for (facet, count, selected) in response.facets[facet]:
        #         print(facet, ' (SELECTED):' if selected else ':', count)

        for hit in response:

            if hit.meta.index == "planthub_datasets_index":
                hits.append({'score': round(hit.meta.score, 3), 'title': hit.title, 'genus': hit.genus})

        list_order['title'] = 1
        list_order["genus"] = 2
        list_order["family"] = 3
        list_order["superorder"] = 4
        list_order["variable"] = 5
        list_order["variable_type"] = 6
        list_order["order"] = 7
        list_order["species"] = 8

        facets_ordered = []
        print(response.facets.__dict__)
        for facet in response.facets:
            for (facet_, count, selected) in response.facets[facet]:
                if len(facet_) > 0:
                    if facet not in facets:
                        facets[facet] = []
                        genus = ""
                        if selected:
                            for hit in response:
                                if facet in hit:
                                    # print(hit[facet])
                                    # print(hit[facet])
                                    # print(facet)
                                    # print(facet_)
                                    # print(x)
                                    # found = [x for x in hit[facet] if x == facet_]
                                    # print(found)
                                    if (hit[facet][0]['genus']):
                                        genus = hit[facet][0]['genus']
                        facets[facet] = [{'name': facet_, 'count': count, 'genus': genus}]
                        facets_ordered.append({'name': facet, 'order': list_order[facet]})
                    else:
                        genus = ""
                        if selected:
                            for hit in response:
                                #  if facet in ["genus", "family"]:
                                if facet in hit:
                                    # print(hit[facet])
                                    # print(facet)
                                    # print(facet_)
                                    # print(x)
                                    # found = [x for x in hit[facet] if x == facet_]
                                    # print(found)
                                    # if found:
                                    # count_values = count_values + found[0]['sum']

                                    if (hit[facet][0]['genus']):
                                        genus = hit[facet][0]['genus']
                        facets[facet].append({'name': facet_, 'count': count, 'genus': genus})

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
        response3 = s3.execute()

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

        for suggest in response3.suggest.simple_suggestion31[0].options:
            print(suggest.__dict__)
            result.append({'name': suggest._source.variable_name,
                           'cat': 'variable',
                           'id': suggest._source.variable_name.replace(" ", "_")})

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
        #  s = s.suggest('simple_suggestion', search_term, term={'field': 'genus.scientific_name'})
        #   s = s.suggest('simple_suggestion_2', search_term, completion={'field': 'genus.translation.name.completion'})
        #  response = s.execute()
        hits = []
        #  print(response.suggest.simple_suggestion)
        #  print(response.suggest.simple_suggestion_2)
        s = PlantHubDatasetsIndex.search()

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
                "variables.name_full",
                "variables.name_full._2gram",
                "variables.name_full._3gram",
            ]
        )

        response = s.execute()

        for hit in response:
            print(hit.__dict__)
            if hit.meta.index == "planthub_species_index":
                translation = []
                for translations in hit.genus.translation:
                    translation.append({'name': translations.name, 'lang': translations.lang})
                hits.append({'score': round(hit.meta.score, 3), 'title': hit.title,
                             'genus': {'name': hit.genus.scientific_name, 'translation': translation}})

        finalJSON = {'hits': hits, 'facets': []}
        return JsonResponse(finalJSON)
