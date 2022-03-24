from django.urls import path  # ,include

from planthub.kg_query.views import TripleView

# from . import views


app_name = "kg_query"
urlpatterns = [
    path('query', TripleView.as_view())
]
