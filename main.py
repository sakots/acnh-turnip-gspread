import optparse

import pymongo_inmemory

from bind import BindService
from bot import TurnipPriceBotService
from logger import logger


def main():
    opt = parse_option()
    sheetkey, credential, bottoken = opt.sheetkey, opt.credential, opt.bottoken
    logger.info("command line option: ", opt)

    with pymongo_inmemory.MongoClient() as client:
        collection = client["my_db"]["user_bindings"]
        binder = BindService(collection)
        bot = TurnipPriceBotService(sheetkey, 0, credential, bottoken, binder)
        bot.run()


def parse_option():
    parser = optparse.OptionParser()
    parser.add_option(
        "-s", "--sheetkey", action="store", dest="sheetkey", type="string"
    )
    parser.add_option(
        "-c", "--credential", action="store", dest="credential", type="string"
    )
    parser.add_option("--bot-token", action="store", dest="bottoken", type="string")
    opt, _ = parser.parse_args()
    return opt


if __name__ == "__main__":
    main()
