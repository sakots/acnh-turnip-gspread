import datetime
import re
from dataclasses import dataclass
from typing import Optional

import discord
import jaconv

from logger import logger


# TODO: move request classes to new file
class Request:
    pass


@dataclass
class UpdateRequest(Request):
    term: str
    price: Optional[int]


@dataclass
class BindRequest(Request):
    name: str


class ChatError(Exception):
    pass


def preprocess(myself: discord.User, message: discord.Message) -> str:
    """
    - ignore from bot or not mention message
    - remove mention string ('@bot')
    - zenkanku to hankaku for ascii chars
    - lowercase
    - strip
    """
    # reject message from bot
    if message.author.bot:
        raise ValueError("bot message is ignored")
    content: str = message.content.strip()
    # reject unless replay to me
    mention_to_me = next(
        filter(
            lambda m: m.id == myself.id,
            message.mentions),
        None)
    if mention_to_me is None:
        raise ValueError("not mention message is ignored")
    # remove mention string
    command = content.replace("<@!{}>".format(myself.id), " ", -1)
    # zenkaku to hankaku
    command = jaconv.z2h(command, ascii=True)
    # downcase
    command = command.lower()
    # strip
    command = command.strip()
    return command


def parse_update_command(
    command: str, current: datetime.datetime
) -> (str, int):  # term, price
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
        if wd in command:
            weekday = wd
            break
    if "買" in command:
        weekday = "買値"
    if weekday is None:
        weekday = wds[current.weekday() % len(wds)]

    # read am. or pm.
    ampm = None
    for am in ["am", "午前", "ごぜん", "gozen"]:
        if am in command:
            ampm = "AM"
    for pm in ["pm", "ごご", "ごご", "gogo"]:
        if pm in command:
            ampm = "PM"
    if ampm is None:
        ampm = "AM" if current.hour < 12 else "PM"

    if weekday == "買値":
        term: str = weekday
    else:
        term: str = "{}{}".format(weekday, ampm)

    # read price
    price = None
    m = re.search(r"[0-9]+", command)
    if m is not None:
        price = int(m.group())

    if price is None:
        raise ChatError("カブ価を教えて")

    return term, price


class ChatService:
    def __init__(self, user: discord.User):
        # TODO: use
        # https://discordpy.readthedocs.io/ja/latest/api.html#discord.Message.mentions
        self.user: discord.User = user

    def recognize(self, message: discord.Message) -> Request:
        logger.info("message received: %s" % message.content)

        # see https://stackoverflow.com/a/13287083
        message_time: datetime.datetime = message.created_at.replace(
            tzinfo=datetime.timezone.utc
        ).astimezone(tz=None)
        command = preprocess(self.user, message)

        if len(command) == 0:
            raise ChatError("やぁ☆")

        m = re.search(r"^\+(.*)", command)
        if m:
            body = m.group(1).strip()
            term, price = parse_update_command(body, message_time)
            return UpdateRequest(term, price)

        m = re.search(r"^(私は|i am|i'm|im)(.*)", command)
        if m:
            body = m.group(2).strip()
            return BindRequest(body)

        raise ChatError("わかりません")

    def echo(self, message) -> str:
        return message.content
