from typing import Optional, List

import discord

import parse_result
import table
from bind import BindService
from gspreads import GspreadService
from logger import logger
from table import TurnipPriceTableViewService


class RespondService:
    def __init__(self, gspread_service: GspreadService, bind_service: BindService):
        self.gspread_service = gspread_service
        self.bind_service = bind_service

    def respond_to(
            self, message: discord.Message, request: parse_result.ParseResult
    ) -> Optional[str]:
        author: discord.Member = message.author
        if isinstance(request, parse_result.SimplePostRequest):
            return request.content
        elif isinstance(request, parse_result.UpdateRequest):
            return self.handle_update_request(author, request)
        elif isinstance(request, parse_result.HistoryRequest):
            return self.handle_history_request(author)
        elif isinstance(request, parse_result.EmptyUpdateRequest):
            return "カブ価を教えて"
        elif isinstance(request, parse_result.BindRequest):
            return self.handle_bind_request(author, request)
        elif isinstance(request, parse_result.WhoAmIRequest):
            return self.handle_who_am_i_request(author)
        elif isinstance(request, parse_result.IgnorableRequest):
            return None
        elif isinstance(request, parse_result.EchoRequest):
            return message.content
        elif isinstance(request, parse_result.EmptyRequest):
            return "やぁ☆"
        elif isinstance(request, parse_result.UnknownRequest):
            return "分かりません"
        else:
            logger.warn("response not implemented. message id: %s", message.id)
            return "実装されていません"

    def handle_update_request(
            self, author: discord.Member, request: parse_result.UpdateRequest
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
        return (
            "書きました\n"
            "期間: {}, 元の価格: {}, 新しい価格: {}\n"
            "履歴: {} {}".format(
                request.term, org_price, request.price, name, format_history(history)
            )
        )

    def handle_history_request(self, author: discord.Member) -> str:
        # FIXME: dup
        sheet_index = 0
        raw_table = self.gspread_service.get_table(sheet_index)
        table_service = TurnipPriceTableViewService(raw_table)
        name = self.bind_service.find_name(author.id)
        if name is None:
            # FIXME: dup
            return "あなたは {}\n" "スプレッドシートには登録されていません".format(author)
        history = table_service.find_user_history(name)
        if history is None:
            return (
                "あなたは {}\n"
                "スプレッドシートでは {}\n"
                "スプレッドシートであなたを見つけられませんでした".format(author, name)
            )
        return "履歴: {} {}".format(name, format_history(history))

    def handle_bind_request(
            self, author: discord.Member, request: parse_result.BindRequest
    ) -> str:
        try:
            self.bind_service.bind(author.id, request.name)
        except Exception as e:
            logger.error("failed to bind user. error: %s", e, exc_info=True)
            return "%s のスプレッドシートでの名前を覚える際にエラーが発生しました" % author
        logger.info("successfully bound. %s is %s, ", author, request.name)
        return "{} はスプレッドシートで {}\n" "覚えました".format(author, request.name)

    def handle_who_am_i_request(self, author: discord.Member) -> str:
        try:
            name = self.bind_service.find_name(author.id)
        except Exception as e:
            logger.error("failed to find binding. error: %s", e, exc_info=True)
            return "あなたは {}\n" "スプレッドシートでの名前を調べる際にエラーが発生しました".format(author)
        if name is not None:
            logger.info("successfully found name. author: %s, name: %s", author, name)
            return "あなたは {}\n" "スプレッドシートでの名前は {}".format(author, name)
        else:
            logger.info(
                "successfully found name but binding not found. author: %s", author
            )
            return "あなたは {}\n" "スプレッドシートには登録されていません".format(author)


def format_history(history: List[str]) -> str:
    if len(history) != 13:
        raise ValueError("length must be 13")
    res = "%s " % history[0]
    for i in list(range(1, 13, 2)):
        am, pm = history[i], history[i + 1]
        res += " %s/%s" % (format_price(am), format_price(pm))
    return res


def format_price(price) -> str:
    if (price or "").strip() == "":
        price = "-"
    return price
