from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Project
from .serializer import ProjectSerializer


@api_view(['GET'])
def get_projects(request):

    try:
        projects = Project.objects.all()
    except Project.DoesNotExist:
        projects = None

    if projects:
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=200)  # OK
    else:
        return HttpResponse(status=204)  # no content


@api_view(['GET'])
def get_project(request):
    project_id = request.query_params.get("id")

    if project_id:
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            project = None
    else:
        return HttpResponse("id parameter missing", status=400)  # Error

    if project:
        serializer = ProjectSerializer(project)
        return Response(serializer.data, status=200)  # OK
    else:
        return HttpResponse(status=204)  # no content
