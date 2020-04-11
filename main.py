import optparse

import pymongo_inmemory

import gspreads
from bind import BindService
from bot import TurnipPriceBotService
from logger import logger


def main():
    opt = parse_option()
    sheet, credential, bottoken = opt.sheetkey, opt.credential, opt.bottoken
    logger.info(opt)

    gspread_service = gspreads.GspreadService(sheet, credential)

    with pymongo_inmemory.MongoClient() as client:
        collection = client["my_db"]["user_bindings"]
        bind_service = BindService(collection)
        bot = TurnipPriceBotService(gspread_service, bottoken, bind_service)
        bot.run()


def parse_option():
    parser = optparse.OptionParser()
    parser.add_option(
        "--sheet", action="store", dest="sheetkey", type="string"
    )
    parser.add_option(
            "--credential", action="store", dest="credential", type="string"
    )
    parser.add_option("--bot-token", action="store", dest="bottoken", type="string")
    opt, _ = parser.parse_args()
    return opt


if __name__ == "__main__":
    main()
