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

        m = re.search(r"h", normalized_body)
        if m:
            return parse_result.HistoryRequest()

        m = re.search(r"^(私は|iam|i'm|im)(.*)", normalized_body)
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
    content: str = message.content.strip()
    # reject unless replay to me
    mention_to_me = next(filter(lambda m: m.id == myself.id, message.mentions), None)
    if mention_to_me is None:
        raise ValueError("not mention message is ignored")


def remove_mention_str(myself: discord.User, message: discord.Message) -> str:
    """
    remove mention string ('@bot')
    """
    return message.content.replace("<@!%s>" % format(myself.id), " ", -1).strip()


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
        return parse_result.EmptyUpdateRequest()

    return parse_result.UpdateRequest(term, price)
