import pytest
from django.test import RequestFactory

from planthub.users.api.views import UserViewSet
from planthub.users.models import User

pytestmark = pytest.mark.django_db


class TestUserViewSet:
    def test_get_queryset(self, user: User, rf: RequestFactory):
        view = UserViewSet()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert user in view.get_queryset()

    def test_me(self, user: User, rf: RequestFactory):
        view = UserViewSet()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request

        response = view.me(request)

        assert response.data == {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "organization": user.organization,
            "url": f"http://testserver/api/users/{user.username}/",
        }
