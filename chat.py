import datetime
import time
from typing import List, Optional


class ChatService:
    def __init__(self, mention_str: str, users_hint: List[str], terms_hint: List[str], timestamp: float):
        self.mention_str = mention_str
        self.users_hint = users_hint
        self.terms_hint = terms_hint
        self.timestamp = timestamp

    # TODO: 大文字小文字全角半角
    def recognize(self, message) -> (str, str, int):  # user, term, price
        name = message.author.nick or message.author.name  # ニックネーム優先
        command = self.preprocess(message)
        if not command:
            return None, None, None

        args: List[str] = command.split()  # 全角スペースもうまくsplitされる
        length = len(args)
        if length == 0:
            raise ValueError("length 0 is unimplemented")
        if length == 1:
            return name, self.time_to_term(), int(args[0])
        if length == 2:
            if args[0] in self.users_hint:
                return args[0], self.time_to_term(), int(args[1])
            if args[0] in self.terms_hint:
                return name, args[0], int(args[1])
            raise ValueError("わかりません")
        if length == 3:
            return args[0], args[1], int(args[2])

    def echo(self, message) -> str:
        return self.preprocess(message)

    def preprocess(self, message) -> Optional[str]:
        # reject message from bot
        if message.author.bot:
            return None
        content: str = message.content.strip()
        # reject unless replay to me
        if not content.startswith(self.mention_str):
            return None
        # remove mention string
        command = content[len(self.mention_str):].strip()
        return command

    def time_to_term(self):
        dt = datetime.datetime.fromtimestamp(self.timestamp)
        idx: int = dt.fromtimestamp(time.time()).weekday()
        weekday = [char for char in '月火水木金土日'][idx]
        ampm: str = 'AM' if dt.hour < 12 else 'PM'
        return next(term for term in self.terms_hint if weekday in term and ampm in term)
