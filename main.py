'''
sample:
100
つぼ 100
木曜午前 100
つぼ 木曜AM 100
つぼ 木曜am 100
つぼ 木曜ａｍ １００
'''

import asyncio
import csv
import discord
import gspread
import oauth2client
import optparse
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

def get_sheet(name, sheet_index, credential):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credential, scope)
    gc = gspread.authorize(credentials)
    wks = gc.open_by_key(name)
    worksheets = wks.worksheets()
    return worksheets[sheet_index]

def parse_command(command):
    '''
    returns the tuple (user, term, price)
    *now only accept [user] [term] [price] format*
    TODO: make it more robust
    '''
    args = command.split()
    l = len(args)
    if l == 3:
        user = args[0]
        term = args[1]
        price = int(args[2])
        return user, term, price
    else:
        raise ValueError("コマンドが解釈できません")

def update(table, user, term, price):
    '''
    returns the tuple (updated operation list, original history, new history)
    '''
    # find the header row and colmn
    rows = table # just an alias
    cols = list(map(list, zip(*rows)))
    users = next(col for col in cols if 'なまえ' in col) # don't work if there exist the user with the name 'なまえ'
    terms = next(row for row in rows if '月AM' in row) # same as abeve
    histbegin = terms.index('買値') # inclusive range
    histend = histbegin + 13 # exclusive range, 13 = len(Sun, Mon AM, Mon PM, ... , Sat AM, Sat PM)

    # find target indicies of update
    if user not in users:
        raise ValueError('ユーザー {} が見つかりません'.format(user))
    rowid = users.index(user)
    if term not in terms:
        raise ValueError('期間 {} が見つかりません'.format(term))
    colid = terms.index(term)

    # backup
    orghist = table[rowid][histbegin:histend]

    oplist = []
    # update
    table[rowid][colid] = price
    newhist = table[rowid][histbegin:histend]

    return (oplist, orghist, newhist)

class TurnipPriceUpdateService:
    def __init__(self, worksheet):
        self.worksheet = worksheet

        client = discord.Client()
        @client.event
        async def on_ready():
            print('ready')
        @client.event
        async def on_message(message):
            self.on_message(message)
        self.bot_client = client

    def run(self, bottoken):
        self.bot_client.run(bottoken)

    async def on_message(self, message):
        # reject message from bot
        if message.author.bot:
            return
        mention = '<@!{}>'.format(client.user.id)
        content = message.content.strip().split()
        # reject unless replay to me
        if not content.startwith(mention):
            return
        # remove mention string
        command = content[len(mention):].strip()

        user, term, price = parse_command(command)
        table = self.worksheet.get_all_values()

        ops, orghist, newhist = update(table, user, term, price)

        # TODO: execute ops here

        resp = "org: {}, new: {}".format(orghist, newhist)
        await message.channel.send(response)

def main():
    opt = parse_cmdargs()
    sheetkey, credential, bottoken = opt.sheetkey, opt.credential, opt.bottoken
    print(sheetkey, credential, bottoken)

    worksheet = get_sheet(sheetkey, 0, credential)
    service = TurnipPriceUpdateService(worksheet)
    service.run(bottoken)

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
