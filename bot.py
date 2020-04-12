from typing import Optional, List

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
    EmptyRequest,
    UnknownRequest,
    EmptyUpdateRequest,
    EchoRequest,
)
import gspreads
from logger import logger
from table import TurnipPriceTableViewService


class TurnipPriceBotService:
    def __init__(
        self,
        token: str,
        gspread_service: gspreads.GspreadService,
        bind_service: BindService,
    ):
        self.gspread_service = gspread_service
        self.bind_service = bind_service

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
        chat_service = ChatService(self.client.user)
        try:
            request: ParseResult = chat_service.recognize(message)
        except Exception as e:
            logger.error(
                "unknown error occurred. error: %s, message id %s",
                e,
                message.id,
                exc_info=True,
            )
            return
        response = self.handle_request(message, request)
        if response is not None:
            await message.channel.send(response)
            logger.info(
                "message sent. content: %s, in reply to %s", response, message.id
            )

    # TODO: extract to class RequestHandleService
    def handle_request(
        self, message: discord.Message, request: ParseResult
    ) -> Optional[str]:
        author: discord.Member = message.author
        if isinstance(request, SimplePostRequest):
            return request.content
        elif isinstance(request, UpdateRequest):
            return self.handle_update_request(author, request)
        elif isinstance(request, EmptyUpdateRequest):
            return "カブ価を教えて"
        elif isinstance(request, BindRequest):
            return self.handle_bind_request(author, request)
        elif isinstance(request, WhoAmIRequest):
            return self.handle_who_am_i_request(author)
        elif isinstance(request, IgnorableRequest):
            return None
        elif isinstance(request, EchoRequest):
            return request.content
        elif isinstance(request, EmptyRequest):
            return "やぁ☆"
        elif isinstance(request, UnknownRequest):
            return "分かりません"
        else:
            logger.warn("response not implemented. message id: %s", message.id)
            return "実装されていません"

    def handle_update_request(
        self, author: discord.Member, request: UpdateRequest
    ) -> str:
        # get position to write on sheet 0
        sheet_index = 0
        raw_table = self.gspread_service.get_table(sheet_index)
        table_service = TurnipPriceTableViewService(raw_table)
        name = self.bind_service.find_name(author.id)
        position = table_service.find_position(name, request.term)
        if isinstance(position, table.UserNotFound):
            logger.info("user not found on table. user: %s", author)
            return "テーブルからあなたの情報が見つかりません"
        if not isinstance(position, table.Found):
            logger.info(
                "user not found on table. user: %s, request: %s", author, request
            )
            return "テーブルのどこに書けばいいか分かりません"

        # try to write
        row, column = position.user_row, position.term_column
        org_price = format_price(raw_table[row][column])
        try:
            self.gspread_service.update_cell(
                sheet_index, row + 1, column + 1, request.price
            )
        except Exception as e:
            logger.error("failed to write to table. error: %s", e, exc_info=True)
            return "テーブルに書き込めませんでした"

        logger.info(
            "successfully updated. row: %s, column: %s, %s -> %s",
            row,
            column,
            org_price,
            request.price,
        )

        # get history
        _, column_left, column_right = table_service.find_terms_range()
        history = table_service.find_user_history(name)

        logger.info("history: %s", history)
        return "書きました\n" \
               "期間: {}, 元の価格: {}, 新しい価格: {}\n" \
               "履歴: {} {}".format(request.term, org_price, request.price, name, format_history(history))

    def handle_bind_request(self, author: discord.Member, request: BindRequest):
        try:
            self.bind_service.bind(author.id, request.name)
        except Exception as e:
            logger.error("failed to bind user. error: %s", e, exc_info=True)
            return "%s のスプレッドシートでの名前を覚える際にエラーが発生しました" % author
        logger.info("successfully bound. %s is %s, ", author, request.name)
        return "{} はスプレッドシートで {}\n" \
               "覚えました".format(author, request.name)

    def handle_who_am_i_request(self, author: discord.Member):
        try:
            name = self.bind_service.find_name(author.id)
        except Exception as e:
            logger.error("failed to find binding. error: %s", e, exc_info=True)
            return "あなたは {}\n" \
                   "スプレッドシートでの名前を調べる際にエラーが発生しました".format(author)
        if name is not None:
            logger.info("successfully found name. author: %s, name: %s", author, name)
            return "あなたは {}\n" \
                   "スプレッドシートでの名前は {}".format(author, name)
        else:
            logger.info(
                "successfully found name but binding not found. author: %s", author
            )
            return "あなたは {}\n" \
                   "スプレッドシートには登録されていません".format(author)


def format_history(history: List[str]) -> str:
    if len(history) != 13:
        raise ValueError("length must be 13")
    res = "%s " % history[0]
    for i in list(range(1, 13, 2)):
        am, pm = history[i], history[i+1]
        res += " %s/%s" % (format_price(am), format_price(pm))
    return res


def format_price(price) -> str:
    if (price or '').strip() == '':
        price = '-'
    return price
