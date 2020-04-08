import csv
import optparse

from bot import TurnipPriceBotService


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
