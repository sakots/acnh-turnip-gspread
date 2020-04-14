from typing import Optional

import pymongo


class BindService:
    """
    bind user id to row id. it's injective, not one-to-one
    """

    def __init__(self, col: pymongo.collection.Collection):
        self.collection = col

    def bind(self, user_id: int, row_id: int):
        doc = {"user_id": user_id, "row_id": row_id}
        self.collection.replace_one({"user_id": user_id}, doc, upsert=True)

    def find_row_id(self, user_id: int) -> Optional[str]:
        res = self.collection.find_one({"user_id": user_id})
        if res is None:
            return None
        else:
            return res["row_id"]
