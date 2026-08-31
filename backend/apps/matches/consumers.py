from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .realtime import get_match_snapshot, match_group_name


class MatchConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.organization_id = self.scope["url_route"]["kwargs"]["organization_id"]
        self.league_id = self.scope["url_route"]["kwargs"]["league_id"]
        self.season_id = self.scope["url_route"]["kwargs"]["season_id"]
        self.match_id = self.scope["url_route"]["kwargs"]["match_id"]

        if not self.scope["user"].is_authenticated:
            await self.close(code=4401)
            return
        if not await self.user_can_view_match():
            await self.close(code=4403)
            return

        self.group_name = match_group_name(self.match_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json(
            {"type": "match.snapshot", "match": await self.match_snapshot()}
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def match_update(self, event):
        await self.send_json(event["payload"])

    @database_sync_to_async
    def user_can_view_match(self) -> bool:
        from .models import Match

        return Match.objects.filter(
            pk=self.match_id,
            fixture__season_id=self.season_id,
            fixture__season__league_id=self.league_id,
            fixture__season__league__organization_id=self.organization_id,
            fixture__season__league__organization__memberships__user_id=self.scope[
                "user"
            ].id,
        ).exists()

    @database_sync_to_async
    def match_snapshot(self) -> dict:
        return get_match_snapshot(self.match_id)
