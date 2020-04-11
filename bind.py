from typing import Optional

import pymongo


class BindService:
    """
    bind id to name. it's injective, not one-to-one
    """

    def __init__(self, col: pymongo.collection.Collection):
        self.collection = col

    def bind(self, id_: int, name: str):
        doc = {"id": id_, "name": name}
        self.collection.replace_one({"id": id_}, doc, upsert=True)

    def find_name(self, id_: int) -> Optional[str]:
        res = self.collection.find_one({"id": id_})
        if res is None:
            return None
        else:
            return res["name"]
