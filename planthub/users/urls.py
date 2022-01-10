from django.urls import path  # ,include
from knox import views as knox_views
from . import views

from planthub.users.views import user_detail_view, user_redirect_view, user_update_view

from .api.api import LoginAPI, RegistrationAPI, UserApi, OrganizationAPI

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
    # path('api/auth', include('knox.urls')), # not sure if we need this
    path('register', RegistrationAPI.as_view()),
    path('login', LoginAPI.as_view()),
    path('user', UserApi.as_view()),
    path('logout', knox_views.LogoutView.as_view(), name='knox_logout'),
    path('organizations', OrganizationAPI.as_view(), name="organization")
]
