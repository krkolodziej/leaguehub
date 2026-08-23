from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class OptionalPageNumberPagination(PageNumberPagination):
    """Keep the legacy list shape unless the client asks for pagination."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        if "page" not in request.query_params and "page_size" not in request.query_params:
            return None
        return super().paginate_queryset(queryset, request, view)


def response_for_queryset(queryset, request, serializer_class, view=None, **serializer_kwargs):
    paginator = OptionalPageNumberPagination()
    page = paginator.paginate_queryset(queryset, request, view=view)
    if page is not None:
        serializer = serializer_class(page, many=True, **serializer_kwargs)
        return paginator.get_paginated_response(serializer.data)
    return Response(serializer_class(queryset, many=True, **serializer_kwargs).data)
