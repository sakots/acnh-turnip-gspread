import datetime
import itertools
import re
from dataclasses import dataclass
from typing import List, Optional

import jaconv


@dataclass
class UpdateRequest:
    user: str
    term: str
    price: int


def datetime_to_term(dt: datetime.datetime) -> str:
    name = [char for char in '月火水木金土'] + ['買値']
    idx: int = dt.weekday()
    weekday = name[idx]
    ampm: str
    if idx != 6:
        ampm = 'AM' if dt.hour < 12 else 'PM'
    else:
        ampm = ''
    return '{}{}'.format(weekday, ampm)


def read_term(s: str) -> Optional[str]:
    # normalize into '月AM' or '買値' format
    t = jaconv.z2h(s, ascii=True)
    t = t.replace('曜日', '').replace('曜', '')
    t = t.replace('午前', 'AM').replace('午後', 'PM')
    t = t.upper()
    if t.startswith('AM') or t.startswith('PM'):
        t = t[2:] + t[:2]

    wd = [c for c in '月火水木金']
    ampm = ['AM', 'PM']
    allowed = ['買値'] + ['{}{}'.format(a, b) for a, b in itertools.product(wd, ampm)]
    if t in allowed:
        return t
    return None


def read_price(price: str) -> Optional[int]:
    price = re.sub(r'ベル$', '', price)
    price = jaconv.z2h(price)
    if re.fullmatch(r'[0-9]+', price):
        return int(jaconv.z2h(price, ascii=True))
    return None


def preprocess(mention_str, message) -> str:
    # reject message from bot
    if message.author.bot:
        raise ValueError("bot message is ignored")
    content: str = message.content.strip()
    # reject unless replay to me
    if not content.startswith(mention_str):
        raise ValueError("not mention message is ignored")
    # remove mention string
    command = content[len(mention_str):].strip()
    return command


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

        name: str = message.author.nick or message.author.name  # ニックネーム優先
        if name not in self.users_hint:
            raise ValueError("unknown user")

        message_time: datetime.datetime = message.created_at

        command = preprocess(self.mention_str, message)

        args: List[str] = command.split()  # 全角スペースもうまくsplitされる
        length = len(args)
        if length == 0:
            raise ValueError("no argument")
        if length == 1:
            # e.g. '100'
            term: str = datetime_to_term(message_time)
            price: int = read_price(args[0])
            return UpdateRequest(name, term, price)
        if length == 2:
            # e.g. '木曜午前 100'
            # e.g. '100 木曜午前'
            for t, p in itertools.permutations(args):
                rest = read_term(t)
                resp = read_price(p)
                if (rest is not None) and (resp is not None):
                    return UpdateRequest(name, rest, resp)
            raise ValueError("cannot infer argument type")
        raise ValueError("too many arguments")


    def echo(self, message) -> str:
        return message.content
