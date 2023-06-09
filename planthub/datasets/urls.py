from django.urls.conf import path

from planthub.datasets.views import download_data, download_metadata

# url pattern for dataset queries
app_name = "datasets"
urlpatterns = [
    path('metadata', download_metadata, name='download_metadata'),
    path('data', download_data, name='download_data'),
]
