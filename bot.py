from typing import Optional

import discord

import table
from bind import BindService
from chat import (
    ChatService,
    SimplePostRequest,
    UpdateRequest,
    BindRequest,
    ParseResult,
    WhoAmIRequest,
    IgnorableRequest,
)
import gspreads
from logger import logger
from table import TurnipPriceTableViewService


class TurnipPriceBotService:
    def __init__(
        self,
        worksheet: str,
        sheet_index: int,
        credential: str,
        bot_token: str,
        binder: BindService,
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
        logger.info("message received: ", message)
        chat_service = ChatService(self.client.user)
        try:
            request: ParseResult = chat_service.recognize(message)
        except Exception as e:
            logger.error("unknown error")
            logger.error(e, exc_info=True)
            return
        response = self.handle_request(message, request)
        if response is not None:
            await message.channel.send(response)
            logger.info("message sent: ", response)

    def handle_request(
        self, message: discord.Message, request: ParseResult
    ) -> Optional[str]:
        author: discord.Member = message.author
        # TODO: 各ifの中身をmethodにする
        if isinstance(request, SimplePostRequest):
            return request.content
        elif isinstance(request, UpdateRequest):
            return self.handle_update_request(author, request)
        elif isinstance(request, BindRequest):
            return self.handle_bind_request(author, request)
        elif isinstance(request, WhoAmIRequest):
            return self.handle_who_am_i_request(author)
        elif isinstance(request, IgnorableRequest):
            return None
        else:
            logger.warn(
                "response to message %s is not implemented".format(message.content)
            )
            return "実装されていません"

    def handle_update_request(
        self, author: discord.Member, request: UpdateRequest
    ) -> str:
        table_service = TurnipPriceTableViewService(self.gs.fetch_table())
        name = self.binder.find_name(author.id)
        result = table_service.find_position(name, request.term)
        if isinstance(result, table.UserNotFound):
            return "テーブルからあなたの情報が見つかりません"
        if not isinstance(result, table.Found):
            return "テーブルのどこに書けばいいか分かりません"
        row, column = result.user_row, result.term_column
        org_price = self.gs.table[row][column]
        try:
            self.gs.set(row + 1, column + 1, request.price)
        except Exception as e:
            logger.error("failed to write to table", e, exc_info=True)
            return "テーブルに書き込めませんでした"
        return "org: {}, new: {}".format(org_price, request.price)

    def handle_bind_request(self, author: discord.Member, request: BindRequest):
        try:
            self.binder.bind(author.id, request.name)
        except Exception as e:
            logger.error("failed to bind user", e, exc_info=True)
            return "名前を覚える際にエラーが発生しました"
        return "覚えました: {} は {}".format(author, request.name)

    def handle_who_am_i_request(self, author: discord.Member):
        try:
            name = self.binder.find_name(author.id)
        except Exception as e:
            logger.error(e, exc_info=True)
            return "あなたは {}\nスプレッドシートでの名前を調べる際にエラーが発生しました".format(author)
        if name is not None:
            return "あなたは {}\nスプレッドシートでの名前は {}".format(author, name)
        else:
            return "あなたは {}\nスプレッドシートには登録されていません".format(author)
