from typing import Optional, List

import discord

import parse_result
import response
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
    ) -> Optional[response.Response]:
        author: discord.Member = message.author
        # FIXME: remove too many if. resolve handler method by type(request).__name__ ?
        if isinstance(request, parse_result.SimplePostRequest):
            return response.plain(request.content)
        elif isinstance(request, parse_result.UpdateRequest):
            return self.handle_update_request(author, request)
        elif isinstance(request, parse_result.HistoryRequest):
            return self.handle_history_request(author)
        elif isinstance(request, parse_result.InvalidUpdateRequest):
            # TODO: @[kabu] を外部から注入する
            return response.warning(
                title="カブ価と期間が分かりません",
                description="正しく入力されていますか？\n"
                "- `@[kabu] 100` -> 現在時刻で登録\n"
                "- `@[kabu] 100 月AM` -> 売値を期間を指定して登録\n"
                "- `@[kabu] 100 買い` -> 買値登録: ",
            )
        elif isinstance(request, parse_result.BindRequest):
            return self.handle_bind_request(author, request)
        elif isinstance(request, parse_result.WhoAmIRequest):
            return self.handle_who_am_i_request(author)
        elif isinstance(request, parse_result.IgnorableRequest):
            return None
        elif isinstance(request, parse_result.EchoRequest):
            return response.plain(message.content)
        elif isinstance(request, parse_result.EmptyRequest):
            return response.plain("やぁ☆")
        elif isinstance(request, parse_result.UnknownRequest):
            logger.warning("unknown message. message id: %s", message.id)
            return response.warning(description="分かりません。")
        else:
            logger.warning("response not implemented. message id: %s", message.id)
            return response.warning(description="実装されていません。")

    def handle_update_request(
        self, author: discord.Member, request: parse_result.UpdateRequest
    ) -> response.Response:
        # get position to write on sheet 0
        sheet_index = 0
        raw_table = self.gspread_service.get_table(sheet_index)
        table_service = TurnipPriceTableViewService(raw_table)
        name = self.bind_service.find_name(author.id)
        if name is None:
            # TODO: スプレッドシートのURLを貼る
            return response.warning(
                title="スプレッドシートでの名前が bot に登録されていません",
                description="スプレッドシートに名前を入力してから `@[kabu] im [スプレッドシートでの名前]`"
                " とリプライして登録してください。",
            )
        position = table_service.find_position(name, request.term)
        if isinstance(position, table.UserNotFound):
            logger.info("user not found on table. user: %s", author)
            return response.warning(
                title="スプレッドシートからあなたの名前が見つかりません",
                description="bot に登録された名前 `%s` は正しいですか？" % name,
            )
        if not isinstance(position, table.Found):
            logger.error(
                "user not found on table. user: %s, request: %s", author, request
            )
            return response.error(
                title="スプレッドシートのどこに書けばいいか分かりません", description="開発者は確認してください。"
            )

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
            return response.error(
                title="スプレッドシートへの書き込みに失敗しました", description="開発者は確認してください。"
            )

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
        if org_price == "-":
            change = "%s %s" % (request.term, request.price)
        else:
            change = "%s %s→%s" % (request.term, org_price, request.price)
        hist = "%s (%s)" % (format_history(history), prediction_link("予測", history))
        return response.success(
            title="スプレッドシートに書きました",
            fields=[
                ("変更内容", change),
                ("名前", "`%s`" % name),
                ("履歴", hist),
            ],
        )

    def handle_history_request(
        self, author: discord.Member
    ) -> Optional[response.Response]:
        # FIXME: dup
        sheet_index = 0
        raw_table = self.gspread_service.get_table(sheet_index)
        table_service = TurnipPriceTableViewService(raw_table)
        name = self.bind_service.find_name(author.id)
        if name is None:
            # FIXME: dup
            return response.warning(
                title="スプレッドシートでの名前が bot に登録されていません",
                description="スプレッドシートに名前を入力してから `@[kabu] im [スプレッドシートでの名前]`"
                " とリプライして登録してください。",
            )
        history = table_service.find_user_history(name)
        if history is None:
            return response.warning(
                title="スプレッドシートからあなたの名前が見つかりません",
                description="bot に登録された名前 `%s` は正しいですか？" % name,
            )
        return response.success(
            title="履歴です",
            fields=[("履歴", format_history(history)), ("予測", prediction_link("Turnip Prophet", history))],
        )

    def handle_bind_request(
        self, author: discord.Member, request: parse_result.BindRequest
    ) -> Optional[response.Response]:
        try:
            self.bind_service.bind(author.id, request.name)
        except Exception as e:
            logger.error("failed to bind user. error: %s", e, exc_info=True)
            return response.error(
                title="スプレッドシートでの名前を覚える際にエラーが発生しました", description="開発者は確認してください。"
            )
        logger.info("successfully bound. %s is %s, ", author, request.name)
        return response.success(
            title="覚えました",
            description="%s はスプレッドシートで `%s`。" % (author.display_name, request.name),
        )

    def handle_who_am_i_request(
        self, author: discord.Member
    ) -> Optional[response.Response]:
        name = self.bind_service.find_name(author.id)
        if name is not None:
            logger.info("successfully found name. author: %s, name: %s", author, name)
            return response.success(
                title="覚えてます",
                description="bot に登録された %s のスプレッドシートでの名前は %s です。" % (author.display_name, name),
            )
        else:
            logger.info(
                "successfully found name but binding not found. author: %s", author
            )
            # FIXME: dup
            return response.warning(
                title="スプレッドシートでの名前が bot に登録されていません",
                description="スプレッドシートに名前を入力してから `@[kabu] im [スプレッドシートでの名前]`"
                " とリプライして登録してください。",
            )


def format_history(history: List[str]) -> str:
    if len(history) != 13:
        raise ValueError("length must be 13")
    last = 0
    for i, h in enumerate(history):
        if (h is None) or (not h):
            continue
        s = str(h).strip()
        if s == "" or s == "-":
            continue
        last = i
    res = "%s" % history[0]
    for i in range(1, last + 1):
        res += "/ "[i % 2]
        res += format_price(history[i])
    return res


def format_price(price) -> str:
    if (price or "").strip() == "":
        price = "-"
    return price


def prediction_url(history: List[str]) -> str:
    """
    予測ツールのURLを返す 最後までURL判定されるように末尾に&を付ける
    https://turnipprophet.io/?prices=100.50.40..........&
    """
    if len(history) != 13:
        raise ValueError("length must be 13")
    a = ".".join(map(lambda x: "" if x is None else str(x).strip(), history))
    return "https://turnipprophet.io/?prices=%s&" % a


def prediction_link(text: str, history: List[str]) -> str:
    """
    予測ツールのURLをマークダウンのリンクのフォーマットにして返す
    https://turnipprophet.io/?prices=100.50.40..........&
    """
    return "[%s](%s)" % (text, prediction_url(history))
