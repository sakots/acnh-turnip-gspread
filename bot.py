import discord

from bind import BindService
from chat import ChatService, ChatError, UpdateRequest, BindRequest, Request
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
            print("ready")

        @self.client.event
        async def on_message(message):
            await self.on_message(message)

    def run(self):
        self.client.run(self.bot_token)

    async def on_message(self, message: discord.Message):
        self.gs.fetch_table()
        chat = ChatService(self.client.user)

        try:
            request: Request = chat.recognize(message)
        except ChatError as e:
            await message.channel.send(e)
            return
        except NotImplemented as e:
            logger.info(e)
            await message.channel.send("実装されていません")
            return
        except AssertionError as e:
            logger.error(e, exc_info=True)
            await message.channel.send("チャットエラー")
            return

        author: discord.Member = message.author
        if isinstance(request, UpdateRequest):
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
