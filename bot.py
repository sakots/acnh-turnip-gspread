import discord

import gspreads
import parse_result
from bind import BindService
from logger import logger
from parse import ParseService
from respond import RespondService


class TurnipPriceBotService:
    def __init__(
        self,
        token: str,
        gspread_service: gspreads.GspreadService,
        bind_service: BindService,
    ):
        self.respond_service = RespondService(gspread_service, bind_service)
        self.bot_token = token
        self.client = discord.Client()

        @self.client.event
        async def on_ready():
            logger.info("bot is ready")

        @self.client.event
        async def on_message(message):
            await self.on_message(message)

    def run(self):
        self.client.run(self.bot_token)

    async def on_message(self, message: discord.Message):
        logger.info(
            "message received. content: %s, id: %s, details: %s",
            message.content,
            message.id,
            message,
        )

        # parse message by parse_service
        parse_service = ParseService(self.client.user)
        try:
            request: parse_result.ParseResult = parse_service.recognize(message)
        except Exception as e:
            logger.error(
                "unknown error occurred on parser. error: %s, message id %s",
                e,
                message.id,
                exc_info=True,
            )
            return

        # respond to message by self.respond_service
        response = self.respond_service.respond_to(message, request)
        if response is not None:
            await message.channel.send(response.content, embed=response.embed)
            logger.info(
                "message sent. response: %s, in reply to %s", response, message.id
            )
