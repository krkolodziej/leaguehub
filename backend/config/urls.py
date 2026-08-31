"""URL configuration for the LeagueHub backend."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.common.views import SpaIndexView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.organizations.urls")),
    path("api/v1/", include("apps.competitions.urls")),
    path("api/v1/", include("apps.matches.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/", include("apps.common.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

# Only when a compiled SPA is bundled alongside the API. Everything Django owns
# is excluded, so the catch-all can never shadow an endpoint or the admin.
if settings.SPA_ROOT:
    urlpatterns += [
        re_path(
            r"^(?!api/|admin/|static/|media/|ws/).*$",
            SpaIndexView.as_view(),
            name="spa-index",
        ),
    ]
