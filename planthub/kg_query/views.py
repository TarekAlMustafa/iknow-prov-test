from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView

from .models import send_request_to_blazegraph


# Create your views here.
class TripleView(APIView):
    # workaround for testing
    # this decorator disables csrf cookie validation
    @csrf_exempt
    def post(self, request):

        json_content = send_request_to_blazegraph()

        # TODO add function to preprocess return values, if needed
        return JsonResponse(json_content)
