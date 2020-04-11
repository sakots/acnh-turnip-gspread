import optparse

import pymongo
import pymongo_inmemory

import gspreads
from bind import BindService
from bot import TurnipPriceBotService
from logger import logger


def main():
    opt = parse_option()
    logger.info("cli option: %s", opt)
    sheet, credential, bottoken = opt.sheetkey, opt.credential, opt.bottoken
    mongodb_host = opt.mongodb_host

    gspread_service = gspreads.GspreadService(sheet, credential)
    if mongodb_host is None:
        logger.info("use pymongo_inmemory client")
        mongodb = pymongo_inmemory.MongoClient()
    else:
        logger.info("create pymongo client")
        mongodb = pymongo.MongoClient("mongodb://%s" % mongodb_host)
    collection = mongodb["turnip_db"]["user_bindings"]
    bind_service = BindService(collection)

    bot = TurnipPriceBotService(bottoken, gspread_service, bind_service)
    bot.run()

    mongodb.close()

def parse_option():
    parser = optparse.OptionParser()
    parser.add_option("--sheet", action="store", dest="sheetkey", type="string")
    parser.add_option("--credential", action="store", dest="credential", type="string")
    parser.add_option("--bot-token", action="store", dest="bottoken", type="string")
    parser.add_option("--mongodb-host", action="store", dest="mongodb_host", type="string")
    opt, _ = parser.parse_args()
    return opt


if __name__ == "__main__":
    main()
