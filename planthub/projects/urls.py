from django.urls.conf import path

from .views import get_project, get_projects

# url pattern for projects queries
app_name = "projects"
urlpatterns = [
    path('all_projects', get_projects, name='get_projects'),
    path('project', get_project, name='get_project'),
]
