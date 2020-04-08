import discord

from chat import ChatService
import gspreads


class TurnipPriceBotService:
    def __init__(self, worksheet: str, sheet_index: int, credential: str, bot_token: str):
        self.gs = gspreads.GspreadService(worksheet, sheet_index, credential)
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
        users = gspreads.users(self.gs.table)
        chat = ChatService(mention)
        request = chat.recognize(message)
        if request is None:
            return

        # TODO: resolve user here
        row, column = gspreads.find_position(self.gs.table, request.user, request.term)
        org_price = self.gs.table[row][column]
        self.gs.set(row + 1, column + 1, request.price)
        response = "org: {}, new: {}".format(org_price, request.price)
        if response:
            await message.channel.send(response)
