import discord

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
        chat = ChatService(mention, self.gs.users())
        request = chat.recognize(message)
        if request is None:
            return

        row, column = find_position(self.gs.table, request.user, request.term)
        org_price = self.gs.table[row][column]
        self.gs.set(row + 1, column + 1, request.price)
        response = "org: {}, new: {}".format(org_price, request.price)
        if response:
            await message.channel.send(response)
