from django.urls import path  # ,include

from .views import Elasticsearch, ElasticsearchSuggest

# from . import views


app_name = "search"
urlpatterns = [
    path('query', Elasticsearch.as_view()),
    path('suggest', ElasticsearchSuggest.as_view()),
]
