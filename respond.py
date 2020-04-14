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
        # FIXME: remove too many if. resolve handler method by type(request).__name__ ?
        if isinstance(request, parse_result.SimplePostRequest):
            return request.content
        elif isinstance(request, parse_result.UpdateRequest):
            return self.handle_update_request(author, request)
        elif isinstance(request, parse_result.HistoryRequest):
            return self.handle_history_request(author)
        elif isinstance(request, parse_result.InvalidUpdateRequest):
            # TODO: @[kabu] を外部から注入する
            return (
                "カブ価と期間は正しく入力されていますか？\n"
                "現在時刻で登録: `@[kabu] +100`\n"
                "売値を期間を指定して登録: `@[kabu] +100 月AM` (曜日と午前午後の両方必要です)"
                "買値登録: `@[kabu] +100 買い`"
            )
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
            return "分かりません。"
        else:
            logger.warn("response not implemented. message id: %s", message.id)
            return "実装されていません。"

    def handle_update_request(
        self, author: discord.Member, request: parse_result.UpdateRequest
    ) -> str:
        # get position to write on sheet 0
        sheet_index = 0
        raw_table = self.gspread_service.get_table(sheet_index)
        table_service = TurnipPriceTableViewService(raw_table)
        name = self.bind_service.find_name(author.id)
        if name is None:
            return (
                "スプレッドシートでの名前が bot に登録されていません。\n"
                "スプレッドシートに名前を入力してから `@[kabu] iam [スプレッドシートでの名前]` とリプライして登録してください。"
            )
        position = table_service.find_position(name, request.term)
        if isinstance(position, table.UserNotFound):
            logger.info("user not found on table. user: %s", author)
            return "スプレッドシートからあなたの名前が見つかりませんでした。\n" "bot に登録された名前 `%s` は正しいですか？" % name
        if not isinstance(position, table.Found):
            logger.error(
                "user not found on table. user: %s, request: %s", author, request
            )
            return "[error] スプレッドシートのどこに書けばいいか分かりません。\n" "開発者は確認してください。"

        # try to write
        row, column = position.user_row, position.term_column
        org_price = format_price(raw_table[row][column])
        try:
            table_service.table[row][column] = str(request.price)
            table_service.trans[column][row] = str(request.price)
            self.gspread_service.update_cell(
                sheet_index, row + 1, column + 1, request.price
            )
        except Exception as e:
            logger.error("failed to write to table. error: %s", e, exc_info=True)
            return "[error] スプレッドシートへの書き込みに失敗しました。\n" "開発者は確認してください。"

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
            "スプレッドシートに書きました。\n"
            "期間: {} | 元の価格: {} | 新しい価格: {} | スプレッドシートでの名前: `{}`\n"
            "履歴: {}\n"
            "書き込んだセル: 行{} 列{} (0始まり)".format(
                request.term,
                org_price,
                request.price,
                name,
                format_history(history),
                row,
                column,
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
            return (
                "スプレッドシートでの名前が bot に登録されていません。\n"
                "スプレッドシートに名前を入力してから `@[kabu] iam [スプレッドシートでの名前]` とリプライして登録してください。"
            )
        history = table_service.find_user_history(name)
        if history is None:
            return "スプレッドシートからあなたの名前が見つかりませんでした。\n" "bot に登録された名前 `%s` は正しいですか？" % name
        return "{}の履歴: {}".format(name, format_history(history))

    def handle_bind_request(
        self, author: discord.Member, request: parse_result.BindRequest
    ) -> str:
        try:
            self.bind_service.bind(author.id, request.name)
        except Exception as e:
            logger.error("failed to bind user. error: %s", e, exc_info=True)
            return "%s のスプレッドシートでの名前を覚える際にエラーが発生しました。" % author
        logger.info("successfully bound. %s is %s, ", author, request.name)
        return "{} はスプレッドシートで `{}`。\n" "覚えました。".format(author, request.name)

    def handle_who_am_i_request(self, author: discord.Member) -> str:
        name = self.bind_service.find_name(author.id)
        if name is not None:
            logger.info("successfully found name. author: %s, name: %s", author, name)
            return "bot に登録された {} のスプレッドシートでの名前は {} です。".format(author, name)
        else:
            logger.info(
                "successfully found name but binding not found. author: %s", author
            )
            return (
                "{} のスプレッドシートでの名前は bot に登録されていません。\n"
                "スプレッドシートに名前を入力してから `@[kabu] iam [スプレッドシートでの名前]` とリプライして登録してください。".format(
                    author
                )
            )


def format_history(history: List[str]) -> str:
    if len(history) != 13:
        raise ValueError("length must be 13")
    res = "%s" % history[0]
    for i in list(range(1, 13, 2)):
        am, pm = history[i], history[i + 1]
        res += " %s/%s" % (format_price(am), format_price(pm))
    return res


def format_price(price) -> str:
    if (price or "").strip() == "":
        price = "-"
    return price
