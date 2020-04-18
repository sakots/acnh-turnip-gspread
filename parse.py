import datetime
import re

import discord
import jaconv

import parse_result
from logger import logger


class ParseService:
    """
    parse discord.Message and convert it to ConvertResult
    """

    def __init__(self, user: discord.User):
        self.user: discord.User = user

    def recognize(self, message: discord.Message) -> parse_result.ParseResult:
        # see https://stackoverflow.com/a/13287083
        message_time: datetime.datetime = message.created_at.replace(
            tzinfo=datetime.timezone.utc
        ).astimezone(tz=None)

        try:
            validate(self.user, message)
        except ValueError as e:
            logger.info(e)
            return parse_result.IgnorableRequest(str(e))

        raw_body = remove_mention_str(self.user, message)
        normalized_body = normalize(raw_body)

        if len(normalized_body) == 0:
            return parse_result.EmptyRequest()

        m = re.search(r"^\+(.*)", normalized_body)
        if m:
            return parse_update_command(m.group(1).strip(), message_time)
        m = re.search(r"^[0-9].*", normalized_body)
        if m:
            return parse_update_command(m.group().strip(), message_time)

        m = re.search(r"^hist", normalized_body)
        if m:
            return parse_result.HistoryRequest()

        m = re.search(r"^(im)(.*)", normalized_body)
        if m:
            prefix_length = len(m.group(1))
            name = raw_body[prefix_length:].strip()
            return parse_result.BindRequest(name)

        m = re.search(r"^who", normalized_body)
        if m:
            return parse_result.WhoAmIRequest()

        m = re.search(r"^echo", normalized_body)
        if m:
            return parse_result.EchoRequest(raw_body)

        return parse_result.UnknownRequest()


def validate(myself: discord.User, message: discord.Message):
    """
    ignore message from bot and not mention
    """
    # reject message from bot
    if message.author.bot:
        raise ValueError("bot message is ignored")
    # reject unless replay to me
    mention_to_me = next(filter(lambda m: m.id == myself.id, message.mentions), None)
    if mention_to_me is None:
        raise ValueError("not mention message is ignored")


def remove_mention_str(myself: discord.User, message: discord.Message) -> str:
    """
    remove mention string ('@bot')
    """
    content: str = message.content
    content = content.replace("<@!%s>" % myself.id, " ", -1)
    content = content.replace("<@%s>" % myself.id, " ", -1)
    return content.strip()


def normalize(command: str) -> str:
    """
    - zenkanku to hankaku for ascii chars
    - lowercase
    - strip
    """
    command: str = command.strip()
    # zenkaku to hankaku
    command = jaconv.z2h(command, kana=False, digit=True, ascii=True)
    # downcase
    command = command.lower()
    # strip
    command = command.strip()
    return command


def parse_update_command(
    normalized_command: str, current: datetime.datetime
) -> parse_result.ParseResult:
    """
    半角小文字に正規化された更新コマンドをパースする
    example:
    - 午前 100
    - 100 午前
    - 100 am
    - 100
    - 月 100
    - 買い 100
    - 買値 100
    """

    ISO_WEEKDAYS = ["買値", "月", "火", "水", "木", "金", "土"]
    TERMS = [
        "買値",
        "買値",
        "月AM",
        "月PM",
        "火AM",
        "火PM",
        "水AM",
        "水PM",
        "木AM",
        "木PM",
        "金AM",
        "金PM",
        "土AM",
        "土PM",
    ]

    # read price
    price = None
    m = re.search(r"[0-9]+", normalized_command)
    if m is not None:
        price = int(m.group())
    if price is None:
        return parse_result.InvalidUpdateRequest()

    # read term or use current if not given
    # read weekday
    weekday = None
    for wd in ISO_WEEKDAYS:
        if wd in normalized_command:
            weekday = wd
            break
    if "買" in normalized_command:
        weekday = "買値"

    # read am. or pm.
    ampm = None
    for am in ["am", "午前", "ごぜん", "gozen"]:
        if am in normalized_command:
            ampm = "AM"
    for pm in ["pm", "午後", "ごご", "gogo"]:
        if pm in normalized_command:
            ampm = "PM"

    # どちらも指定されていない
    if weekday != "買値" and (weekday is None) != (ampm is None):
        logger.info(
            "invalid update request. none or both of weekday and ampm must be specified. weekday=%s, ampm=%s",
            weekday,
            ampm,
        )
        return parse_result.InvalidUpdateRequest()
    # use current
    backward = False
    if (weekday is None) and (ampm is None):
        logger.info("term is not specified. use current time")
        weekday = ISO_WEEKDAYS[current.isoweekday() % len(ISO_WEEKDAYS)]
        ampm = "AM" if current.hour < 12 else "PM"
        backward = current.hour < 5

    if weekday == "買値":
        term: str = weekday
    else:
        term: str = "{}{}".format(weekday, ampm)

    # 午前5時前なら1つ戻す
    if backward:
        logger.info("term is not specified and hour=%s, go backward", current.hour)
        index = TERMS.index(term)
        term = TERMS[(index - 1) % len(TERMS)]  # (-1) % 3 == 2 in Python
    return parse_result.UpdateRequest(term, price)
