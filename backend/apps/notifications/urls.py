from django.urls import path

from .views import NotificationListView, NotificationReadView

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path(
        "notifications/<int:notification_id>/read/",
        NotificationReadView.as_view(),
        name="notification-read",
    ),
]
