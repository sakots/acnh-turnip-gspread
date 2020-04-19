import discord

import gspreads
import parse_result
from bind import BindService
from logger import logger
from parse import ParseService
from respond import RespondService


class TurnipPriceBot(discord.Client):
    def __init__(self, token: str, gspread_service: gspreads.GspreadService, bind_service: BindService, **options):
        super().__init__(**options)
        self.bot_token = token
        self.gspread_service = gspread_service
        self.respond_service = None
        self.bind_service = bind_service

    def run(self):
        super().run(self.bot_token)

    async def on_ready(self):
        logger.info("bot is ready. name: %s, id:%s", self.user.name, self.user.id)
        logger.info("joining guilds:")
        for g in self.guilds:
            g: discord.Guild
            logger.info("* %s (%s)", g.name, g.id)
        self.respond_service = RespondService(self.user, self.gspread_service, self.bind_service)

    async def on_message(self, message: discord.Message):
        logger.info(
            "message received. content: %s, id: %s, details: %s",
            message.content,
            message.id,
            message,
        )

        # parse message by parse_service
        parse_service = ParseService(self.user)
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
                "message sent in reply to %s, content: %s", message.id, response.content
            )
            if response.embed is not None:
                embed = response.embed
                logger.info(
                    "reply to %s contains embed. title: %s, description: %s, fields: %s",
                    message.id,
                    embed.title,
                    embed.description,
                    embed.fields,
                )
