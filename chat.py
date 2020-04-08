import datetime
import re
from dataclasses import dataclass
from typing import List, Optional

import jaconv


@dataclass
class UpdateRequest:
    user: str
    term: str
    price: Optional[int]


def preprocess(mention_str, message) -> str:
    """
    - ignore from bot or not mention message
    - remove mention string
    - zenkanku to hankaku for ascii chars
    - lowercase
    - strip
    """
    # reject message from bot
    if message.author.bot:
        raise ValueError("bot message is ignored")
    content: str = message.content.strip()
    # reject unless replay to me
    if not content.startswith(mention_str):
        raise ValueError("not mention message is ignored")
    # remove mention string
    command = content[len(mention_str):].strip()
    # zenkaku to hankaku
    command = jaconv.z2h(command, ascii=True)
    # downcase
    command = command.lower()
    # strip
    command = command.strip()
    return command


def parse_update_command(command: str, current: datetime.datetime) -> (str, int):  # term, price
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
    wds = ['月', '火', '水', '木', '金', '土', '買値']
    for wd in wds:
        if wd in command:
            weekday = wd
            break
    if '買' in command:
        weekday = '買値'
    if weekday is None:
        weekday = wds[current.weekday() % len(wds)]

    # read am. or pm.
    ampm = None
    for am in ['am', '午前', 'ごぜん', 'gozen']:
        if am in command:
            ampm = 'AM'
    for pm in ['pm', 'ごご', 'ごご', 'gogo']:
        if pm in command:
            ampm = 'PM'
    if ampm is None:
        ampm = 'AM' if current.hour < 12 else 'PM'

    if weekday == '買値':
        term: str = weekday
    else:
        term: str = '{}{}'.format(weekday, ampm)

    # read price
    price = None
    m = re.search(r'[0-9]+', command)
    if m is not None:
        price = int(m.group())

    return term, price


class ChatService:
    def __init__(self, mention_str: str, users_hint: List[str]):
        self.mention_str = mention_str
        self.users_hint = users_hint

    def recognize(self, message) -> UpdateRequest:
        """
        sample:
        100
        木曜午前 100
        木曜AM 100
        木曜am 100
        木曜ａｍ １００
        am木 100
        100 木曜午前
        """

        # nickname is preferred
        user: str = message.author.nick or message.author.name
        if user not in self.users_hint:
            raise ValueError("unknown user")
        message_time: datetime.datetime = message.created_at

        command = preprocess(self.mention_str, message)
        if len(command) == 0:
            raise ValueError("empty body")

        m = re.search(r'^\+(.*)', command)
        if m:
            body = m.group(1).strip()
            term, price = parse_update_command(body, message_time)
            return UpdateRequest(user, term, price)

        m = re.search(r"^(私は|i am|i'm|im)(.*)", command)
        if m:
            body = m.group(2).strip()
            raise NotImplemented

        raise ValueError("unknown command")


    def echo(self, message) -> str:
        return message.content
