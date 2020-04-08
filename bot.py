import discord

from chat import ChatService, ChatError
import gspreads
from main import logger


class TurnipPriceBotService:
    def __init__(self, worksheet: str, sheet_index: int, credential: str, bot_token: str):
        self.gs = gspreads.GspreadService(worksheet, sheet_index, credential)
        self.bot_token = bot_token
        self.client = discord.Client()

        # TODO: inject handler from arguments
        @self.client.event
        async def on_ready():
            print('ready')

        @self.client.event
        async def on_message(message):
            await self.on_message(message)

    def run(self):
        self.client.run(self.bot_token)

    async def on_message(self, message: discord.Message):
        self.gs.fetch_table()
        chat = ChatService(self.client.user)

        try:
            request = chat.recognize(message)
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

        # TODO: enable to bind discord user id and user name on table by command
        # TODO: currently use message author's nickname or name
        try:
            user = message.author.nick or message.author.name
            row, column = gspreads.find_position(self.gs.table, user, request.term)
            org_price = self.gs.table[row][column]
            self.gs.set(row + 1, column + 1, request.price)
        except Exception as e:
            logger.error(e, exc_info=True)
            await message.channel.send("Spreadsheet書き込みエラー")
            return

        response = "org: {}, new: {}".format(org_price, request.price)
        await message.channel.send(response)
