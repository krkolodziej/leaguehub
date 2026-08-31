from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.views import View
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import HealthResponseSerializer


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=HealthResponseSerializer)
    def get(self, request):
        return Response({"status": "ok"})


class SpaIndexView(View):
    """Return the compiled index.html so client-side routes survive a refresh.

    WhiteNoise serves the hashed assets; only unmatched paths reach here, which
    is exactly the set of routes React Router owns.
    """

    def get(self, request, *args, **kwargs):
        if not settings.SPA_ROOT:
            raise Http404
        index = Path(settings.SPA_ROOT) / "index.html"
        if not index.is_file():
            raise Http404
        response = FileResponse(index.open("rb"), content_type="text/html")
        response["Cache-Control"] = "no-cache"
        return response
