import datetime
import itertools
from unittest import TestCase
from unittest.mock import Mock

import jaconv

import chat


def bot():
    bot = Mock()
    bot.id = 1234
    bot.mention = "<@!1234>"
    return bot


def make_massage(content: str):
    message = Mock()
    message.author.bot = False
    message.content = "<@!{}> {}".format(bot().id, content)
    message.created_at = datetime.datetime(2020, 4, 6, 11, 30, 0)
    message.mentions = [bot()]
    return message


class TestChatService(TestCase):
    def test_recognize(self):
        # TODO: test 買値
        botuser = bot()
        service = chat.ChatService(botuser)

        base = ["月曜午前", "月AM", "午前月曜", "AM月", "AM月　　"]
        small = map(lambda x: x.lower(), base)
        ja = map(lambda x: jaconv.h2z(x, ascii=True), base)
        term = list(itertools.chain(base, small, ja))
        ok_cases = ["+100 {}".format(c) for c in term] + [
            "+{} 100".format(c) for c in term
        ]

        for c in ok_cases:
            message = make_massage(c)
            expected = chat.UpdateRequest("月AM", 100)
            self.assertEqual(service.recognize(message), expected)

        bad_cases = [
            "",
            "100 100",
            "月曜AM 月曜AM",
            "a b",
            "100, 月曜AM",
            "買値 100 100"]

        for c in bad_cases:
            with self.assertRaises(ValueError):
                service.recognize(make_massage(c))

    def test_parse_update_command_monday(self):
        current = datetime.datetime(2020, 4, 6, 11, 30, 0)
        testcases = ["月am 100", "月 100", "月　100", "100"]
        for command in testcases:
            term, price = chat.parse_update_command(command, current)
            self.assertEqual("月AM", term)
            self.assertEqual(100, price)

    def test_parse_update_command_sunday(self):
        current = datetime.datetime(2020, 4, 5, 10, 30, 0)
        testcases = ["買い 100", "100"]
        for command in testcases:
            term, price = chat.parse_update_command(command, current)
            self.assertEqual("買値", term)
            self.assertEqual(100, price)
