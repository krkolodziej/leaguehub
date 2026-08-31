import pytest
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.sessions.backends.db import SessionStore
from django.test import override_settings

from apps.matches.models import Match
from config.asgi import application

from .test_matches import make_match_data
from ..realtime import match_group_name


@pytest.mark.django_db(transaction=True)
@override_settings(
    CHANNEL_LAYERS={
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }
)
def test_member_receives_match_snapshot_on_websocket_connect():
    _, member, organization, league, season, fixture, _, _ = make_match_data()
    match = Match.objects.create(fixture=fixture)

    session = SessionStore()
    session["_auth_user_id"] = str(member.pk)
    session["_auth_user_backend"] = "django.contrib.auth.backends.ModelBackend"
    session["_auth_user_hash"] = member.get_session_auth_hash()
    session.save()
    path = (
        f"/ws/organizations/{organization.id}/leagues/{league.id}/"
        f"seasons/{season.id}/matches/{match.id}/"
    )

    async def connect_and_receive():
        communicator = WebsocketCommunicator(
            application,
            path,
            headers=[(b"cookie", f"sessionid={session.session_key}".encode())],
        )
        connected, _ = await communicator.connect()
        assert connected is True
        snapshot = await communicator.receive_json_from()
        assert snapshot["type"] == "match.snapshot"
        assert snapshot["match"]["id"] == match.id
        await get_channel_layer().group_send(
            match_group_name(match.id),
            {
                "type": "match.update",
                "payload": {
                    "type": "match.updated",
                    "match": snapshot["match"],
                },
            },
        )
        update = await communicator.receive_json_from()
        assert update["type"] == "match.updated"
        await communicator.disconnect()

    async_to_sync(connect_and_receive)()
