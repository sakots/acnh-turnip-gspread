'''
sample:
100
つぼ 100
木曜午前 100
つぼ 木曜AM 100
つぼ 木曜am 100
つぼ 木曜ａｍ １００
'''

import csv
import datetime
import optparse
import time
from typing import List, Optional

import discord
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def parse_cmdargs():
    parser = optparse.OptionParser()
    parser.add_option('-s', '--sheetkey', action="store", dest="sheetkey", type="string")
    parser.add_option('-c', '--credential', action="store", dest="credential", type="string")
    parser.add_option('--bot-token', action="store", dest="bottoken", type="string")
    opt, _ = parser.parse_args()
    return opt


def load_testdata(filename):
    table = None
    with open(filename, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        table = [row for row in reader]
        # return table # <- ok?
    return table


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


def find_position(table, user, term) -> (int, int):
    """
    returns the tuple (updated operation list, original history, new history)
    """
    # find the header row and column
    rows = table  # just an alias
    cols = list(map(list, zip(*rows)))
    users = next(col for col in cols if 'なまえ' in col)  # don't work if there exist the user with the name 'なまえ'
    terms = next(row for row in rows if '月AM' in row)  # same as above

    # find target indices of update
    if user not in users:
        raise ValueError('ユーザー {} が見つかりません'.format(user))
    row_id = users.index(user)
    if term not in terms:
        raise ValueError('期間 {} が見つかりません'.format(term))
    column_id = terms.index(term)

    return row_id, column_id


def get_sheet(worksheet: str, sheetindex: int, credential: str) -> gspread.Worksheet:
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credential, scope)
    gc = gspread.authorize(credentials)
    wks = gc.open_by_key(worksheet)
    worksheets = wks.worksheets()
    return worksheets[sheetindex]


class GspreadService:
    def __init__(self, sheetkey: str, sheetindex: int, credential: str):
        self.sheet = get_sheet(sheetkey, sheetindex, credential)
        self.table = None

    def set(self, row, column, value):
        return self.sheet.update_cell(row, column, value)

    def fetch_table(self):
        self.table = self.sheet.get_all_values()

    def users(self) -> List[str]:
        if not self.table:
            raise AssertionError("call fetch_table method before")
        cols = list(map(list, zip(*self.table)))
        # Don't work unless the header string is 'なまえ', and there is no user with name 'なまえ.'
        user_column_identifier = 'なまえ'
        users_column = next(col for col in cols if user_column_identifier in col)
        idx = users_column.index(user_column_identifier)
        return users_column[idx + 1:]

    def terms(self) -> List[str]:
        if not self.table:
            raise AssertionError("call fetch_table method before")
        # See the comment of users
        terms_row_identifier = '買値'
        terms_row = next(row for row in self.table if terms_row_identifier in row)
        idx = terms_row.index(terms_row_identifier)
        return terms_row[idx:idx + 13]


class TurnipPriceBotService:
    def __init__(self, worksheet: str, sheet_index: int, credential: str, bot_token: str):
        self.gs = GspreadService(worksheet, sheet_index, credential)
        self.bot_token = bot_token
        self.client = discord.Client()

        @self.client.event
        async def on_ready():
            print('ready')

        @self.client.event
        async def on_message(message):
            await self.on_message(message)

    def run(self):
        self.client.run(self.bot_token)

    async def on_message(self, message):
        mention = '<@!{}>'.format(self.client.user.id)

        self.gs.fetch_table()
        chat = ChatService(mention, self.gs.users(), self.gs.terms(), time.time())
        user, term, new_price = chat.recognize(message)
        if not user:
            return
        print(user, term, new_price)
        row, column = find_position(self.gs.table, user, term)
        org_price = self.gs.table[row][column]
        self.gs.set(row + 1, column + 1, new_price)
        response = "org: {}, new: {}".format(org_price, new_price)
        if response:
            await message.channel.send(response)


def main():
    opt = parse_cmdargs()
    sheetkey, credential, bottoken = opt.sheetkey, opt.credential, opt.bottoken
    print(sheetkey, credential, bottoken)
    bot = TurnipPriceBotService(sheetkey, 0, credential, bottoken)
    bot.run()

    # prod = False
    # if prod:
    #     ws = get_sheet(sheetkey, 0, credential)
    #     table = ws.get_all_values()
    # else:
    #     table = load_testdata('./testdata.tsv')
    # oplist, org, new = update(table, user, term, price)
    # print(oplist, org, new)


if __name__ == "__main__":
    main()
