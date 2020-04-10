import discord

from bind import BindService
from chat import ChatService, SimplePostRequest, UpdateRequest, BindRequest, ParseResult, WhoAmIRequest, IgnorableRequest
import gspreads
from logger import logger


class TurnipPriceBotService:
    def __init__(
        self, worksheet: str, sheet_index: int, credential: str, bot_token: str, binder: BindService,
    ):
        self.gs = gspreads.GspreadService(worksheet, sheet_index, credential)
        self.bot_token = bot_token
        self.client = discord.Client()
        self.binder = binder

        # TODO: inject handler from arguments
        @self.client.event
        async def on_ready():
            logger.info("ready")

        @self.client.event
        async def on_message(message):
            await self.on_message(message)

    def run(self):
        self.client.run(self.bot_token)

    async def on_message(self, message: discord.Message):
        self.gs.fetch_table()
        chat = ChatService(self.client.user)

        try:
            request: ParseResult = chat.recognize(message)
        except Exception as e:
            logger.error("unknown error: ", e, exc_info=True)
            return

        author: discord.Member = message.author
        if isinstance(request, SimplePostRequest):
            await message.channel.send(request.content)
            return
        elif isinstance(request, UpdateRequest):
            try:
                name = self.binder.find_name(author.id)
                row, column = gspreads.find_position(
                    self.gs.table, name, request.term)
                org_price = self.gs.table[row][column]
                self.gs.set(row + 1, column + 1, request.price)
            except Exception as e:
                logger.error(e, exc_info=True)
                await message.channel.send("Spreadsheet 書き込み時にエラーが発生しました")
                return
            response = "org: {}, new: {}".format(org_price, request.price)
            await message.channel.send(response)
        elif isinstance(request, BindRequest):
            try:
                self.binder.bind(author.id, request.name)
            except Exception as e:
                logger.error(e, exc_info=True)
                await message.channel.send("名前を覚える際にエラーが発生しました")
                return
            response = "覚えました: {} は {}".format(author, request.name)
            await message.channel.send(response)
        elif isinstance(request, WhoAmIRequest):
            try:
                name = self.binder.find_name(author.id)
            except Exception as e:
                logger.error(e, exc_info=True)
                await message.channel.send("名前を調べる際にエラーが発生しました")
                return
            if name is not None:
                response = "あなたは {}\n{}".format(author, name)
            else:
                response = "あなたは {}\n別名は知りません".format(author)
            await message.channel.send(response)
        elif isinstance(request, IgnorableRequest):
            pass
