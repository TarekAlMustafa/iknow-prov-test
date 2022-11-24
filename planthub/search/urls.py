from django.urls import path  # ,include

from .views import (
    Elasticsearch,
    ElasticsearchItem,
    ElasticsearchMatch,
    ElasticsearchSuggest,
)

# from . import views


app_name = "search"
urlpatterns = [
    path('query', Elasticsearch.as_view()),
    path('suggest', ElasticsearchSuggest.as_view()),
    path('suggest_match', ElasticsearchMatch.as_view()),
    path('index_item', ElasticsearchItem.as_view()),
]
