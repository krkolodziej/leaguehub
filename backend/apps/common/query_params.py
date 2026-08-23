from django.db.models import Q
from rest_framework.exceptions import ValidationError


def apply_query_options(
    queryset,
    request,
    *,
    search_fields=(),
    ordering_fields=(),
    default_ordering=(),
):
    search = request.query_params.get("search", "").strip()
    if search and search_fields:
        query = Q()
        for field in search_fields:
            query |= Q(**{f"{field}__icontains": search})
        queryset = queryset.filter(query)

    ordering = request.query_params.get("ordering")
    if ordering:
        allowed = set(ordering_fields)
        requested = [item.strip() for item in ordering.split(",") if item.strip()]
        invalid = [
            item
            for item in requested
            if item.lstrip("-") not in allowed
        ]
        if invalid:
            raise ValidationError(
                {"ordering": f"Unsupported ordering field(s): {', '.join(invalid)}."}
            )
        queryset = queryset.order_by(*requested)
    elif default_ordering:
        queryset = queryset.order_by(*default_ordering)
    return queryset
