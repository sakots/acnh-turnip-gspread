import datetime
import re
from dataclasses import dataclass

import discord
import jaconv

from logger import logger


# TODO: move request classes to new file
class ParseResult:
    pass


@dataclass
class UpdateRequest(ParseResult):
    term: str
    price: int


@dataclass
class HistoryRequest(ParseResult):
    pass


@dataclass
class EmptyUpdateRequest(ParseResult):
    pass


@dataclass
class BindRequest(ParseResult):
    name: str


class WhoAmIRequest(ParseResult):
    pass


@dataclass
class SimplePostRequest(ParseResult):
    content: str


@dataclass
class IgnorableRequest(ParseResult):
    reason: str


@dataclass
class EmptyRequest(ParseResult):
    pass


@dataclass
class EchoRequest(ParseResult):
    content: str


@dataclass
class UnknownRequest(ParseResult):
    pass


def validate(myself: discord.User, message: discord.Message):
    """
    ignore message from bot and not mention
    """
    # reject message from bot
    if message.author.bot:
        raise ValueError("bot message is ignored")
    content: str = message.content.strip()
    # reject unless replay to me
    mention_to_me = next(filter(lambda m: m.id == myself.id, message.mentions), None)
    if mention_to_me is None:
        raise ValueError("not mention message is ignored")


def remove_mention_str(myself: discord.User, message: discord.Message) -> str:
    """
    remove mention string ('@bot')
    """
    return message.content.replace("<@!%s>" % format(myself.id), " ", -1)


def normalize(command: str) -> str:
    """
    - zenkanku to hankaku for ascii chars
    - lowercase
    - strip
    """
    command: str = command.strip()
    # zenkaku to hankaku
    command = jaconv.z2h(command, ascii=True)
    # downcase
    command = command.lower()
    # strip
    command = command.strip()
    return command


def parse_update_command(normalized_command: str, current: datetime.datetime) -> ParseResult:
    """
    example:
    - 午前 100
    - 100 午前
    - 100 am
    - 100
    - 月 100
    - 買い 100
    - 買値 100
    """
    # read weekday
    weekday = None
    wds = ["月", "火", "水", "木", "金", "土", "買値"]
    for wd in wds:
        if wd in normalized_command:
            weekday = wd
            break
    if "買" in normalized_command:
        weekday = "買値"
    if weekday is None:
        weekday = wds[current.weekday() % len(wds)]

    # read am. or pm.
    ampm = None
    for am in ["am", "午前", "ごぜん", "gozen"]:
        if am in normalized_command:
            ampm = "AM"
    for pm in ["pm", "ごご", "ごご", "gogo"]:
        if pm in normalized_command:
            ampm = "PM"
    if ampm is None:
        ampm = "AM" if current.hour < 12 else "PM"

    if weekday == "買値":
        term: str = weekday
    else:
        term: str = "{}{}".format(weekday, ampm)

    # read price
    price = None
    m = re.search(r"[0-9]+", normalized_command)
    if m is not None:
        price = int(m.group())

    if price is None:
        return EmptyUpdateRequest()

    return UpdateRequest(term, price)


class ChatService:
    def __init__(self, user: discord.User):
        self.user: discord.User = user

    def recognize(self, message: discord.Message) -> ParseResult:
        # see https://stackoverflow.com/a/13287083
        message_time: datetime.datetime = message.created_at.replace(
            tzinfo=datetime.timezone.utc
        ).astimezone(tz=None)

        try:
            validate(self.user, message)
        except ValueError as e:
            logger.info(e)
            return IgnorableRequest(str(e))

        body = remove_mention_str(self.user, message)
        normalized_body = normalize(body)

        if len(normalized_body) == 0:
            return EmptyRequest()

        m = re.search(r"^\+(.*)", normalized_body)
        if m:
            body = m.group(1).strip()
            return parse_update_command(body, message_time)

        m = re.search(r"h", normalized_body)
        if m:
            return HistoryRequest()

        m = re.search(r"^(私は|i am|i'm|im)(.*)", normalized_body)
        if m:
            name = m.group(2).strip()
            return BindRequest(name)

        m = re.search(r"^who", normalized_body)
        if m:
            return WhoAmIRequest()

        m = re.search(r"^echo", normalized_body)
        if m:
            return EchoRequest(normalized_body)

        return UnknownRequest()
