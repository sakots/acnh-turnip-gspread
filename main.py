import base64
import json
import os
import urllib.parse
from optparse import OptionParser
import pprint

import yaml

import gspreads
from bind import BindService
from bot import TurnipPriceBotService
from logger import logger


def load_config():
    # load normal options from command line options
    parser = OptionParser()
    parser.add_option(
        "--config", dest="config", help="configuration file path", metavar="FILE"
    )
    option, _ = parser.parse_args()
    config = yaml.load(open(option.config, "r").read(), Loader=yaml.FullLoader)

    # load credentials from environ
    config["gspread_name"] = os.environ.get("GSPREAD_NAME")
    config["gspread_credential_base64"] = os.environ.get("GSPREAD_CREDENTIAL_BASE64")
    config["mongo_host"] = os.environ.get("MONGO_HOST")
    config["mongo_port"] = os.environ.get("MONGO_PORT")
    config["mongo_app_username"] = os.environ.get("MONGO_APP_USERNAME")
    config["mongo_app_password"] = os.environ.get("MONGO_APP_PASSWORD")
    config["discord_bot_token"] = os.environ.get("DISCORD_BOT_TOKEN")

    return config


def main():
    config = load_config()
    logger.info(pprint.pformat(config))

    # gspread
    json_ = base64.b64decode(config["gspread_credential_base64"])
    credential = json.loads(json_)

    gspread_service = gspreads.GspreadService(config["gspread_name"], credential)

    # mongodb
    if config.get("mongodb_use_inmemory") or False:
        logger.info("use pymongo_inmemory client")
        import pymongo_inmemory

        mongodb = pymongo_inmemory.MongoClient()
    else:
        logger.info("create pymongo client")
        username = urllib.parse.quote_plus(config["mongo_app_username"])
        password = urllib.parse.quote_plus(config["mongo_app_password"])
        import pymongo

        mongodb = pymongo.MongoClient(
            config["mongo_host"],
            int(config["mongo_port"]),
            username=username,
            password=password,
            authSource="admin",
        )
    collection = mongodb[config["mongo_database"]][config["mongo_collection"]]

    # bind
    bind_service = BindService(collection)

    bot_service = TurnipPriceBotService(
        config["discord_bot_token"], gspread_service, bind_service
    )
    bot_service.run()

    mongodb.close()


if __name__ == "__main__":
    main()
