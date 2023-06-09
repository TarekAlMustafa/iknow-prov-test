from django.urls import path

from . import views

app_name = 'viz'
urlpatterns = [
    path('', views.choose_plot, name='choose_plot'),
    path('pie', views.pie, name='pie'),
    path('bar', views.bar, name='bar'),
    path('violin', views.violin_view, name='violin'),
    path('scatter_cat', views.scatter_cat, name='scatter_cat'),
    path('scatter_cont', views.scatter_cont, name='scatter_cont'),
    path('scatter_3D_cat', views.scatter_3D_cat, name='scatter_3D_cat'),
    path('scatter_matrix_cat', views.scatter_matrix_cat, name='scatter_matrix_cat'),
    path('histogram', views.histogram, name='histogram'),
    path('get_datasets', views.get_datasets, name='get_datasets'),

]
