import discord
import time

from chat import ChatService
from gspreads import GspreadService, find_position


class TurnipPriceBotService:
    def __init__(self, worksheet: str, sheet_index: int, credential: str, bot_token: str):
        self.gs = GspreadService(worksheet, sheet_index, credential)
        self.bot_token = bot_token
        self.client = discord.Client()

        @self.client.event
        async def on_ready():
            print('ready')

        @self.client.event
        async def on_message(message):
            await self.on_message(message)

    def run(self):
        self.client.run(self.bot_token)

    async def on_message(self, message):
        mention = '<@!{}>'.format(self.client.user.id)

        self.gs.fetch_table()
        chat = ChatService(mention, self.gs.users(), self.gs.terms(), time.time())
        user, term, new_price = chat.recognize(message)
        if not user:
            return
        print(user, term, new_price)
        row, column = find_position(self.gs.table, user, term)
        org_price = self.gs.table[row][column]
        self.gs.set(row + 1, column + 1, new_price)
        response = "org: {}, new: {}".format(org_price, new_price)
        if response:
            await message.channel.send(response)
