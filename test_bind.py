from unittest import TestCase

import pymongo_inmemory

from bind import BindService


class TestMongoNameIdBindService(TestCase):
    def test_bind(self):
        client = pymongo_inmemory.MongoClient()  # No need to provide host
        db = client['testdb']
        collection = db['user_bindings']

        binds = BindService(collection)

        self.assertEqual(binds.find_name(1), None)
        binds.bind(1, "a")
        self.assertEqual(binds.find_name(1), "a")
        binds.bind(1, "b")
        self.assertEqual(binds.find_name(1), "b")
