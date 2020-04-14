import datetime
import itertools
from unittest import TestCase
from unittest.mock import Mock

import jaconv

import parse
import parse_result


class TestParseService(TestCase):
    def test_normalize(self):
        self.assertEqual(parse.normalize("＋１００"), "+100")
        self.assertEqual(parse.normalize("ＡＢＣ"), "abc")

    def test_recognize_update(self):
        botuser = bot()
        service = parse.ParseService(botuser)

        base = ["月曜午前", "月AM", "午前月曜", "AM月", "AM月　　"]
        small = map(lambda x: x.lower(), base)
        ja = map(lambda x: jaconv.h2z(x, kana=False, digit=True, ascii=True), base)
        term = list(itertools.chain(base, small, ja))
        ok_cases = (
            ["+100 {}".format(c) for c in term]
            + ["＋１００ {}".format(c) for c in term]
            + ["+{} 100".format(c) for c in term]
        )

        for c in ok_cases:
            message = make_massage(c)
            expected = parse_result.UpdateRequest("月AM", 100)
            self.assertEqual(service.recognize(message), expected)

    def test_recognize_bind(self):
        botuser = bot()
        service = parse.ParseService(botuser)
        self.assertEqual(
            parse_result.BindRequest("ー"), service.recognize(make_massage("imー"))
        )
        self.assertEqual(
            parse_result.BindRequest("ー"), service.recognize(make_massage("im ー"))
        )
        self.assertEqual(
            parse_result.BindRequest("🍎"), service.recognize(make_massage("im🍎"))
        )

    def test_no_price(self):
        botuser = bot()
        service = parse.ParseService(botuser)
        bad_cases = ["+", "+月曜AM 月曜AM", "+a b"]
        for c in bad_cases:
            result = service.recognize(make_massage(c))
            self.assertEqual(result, parse_result.InvalidUpdateRequest())

    def test_from_bot(self):
        botuser = bot()
        service = parse.ParseService(botuser)
        message = make_massage("+100")
        message.author = botuser
        result = service.recognize(message)
        self.assertTrue(isinstance(result, parse_result.IgnorableRequest))

    def test_not_mention(self):
        botuser = bot()
        service = parse.ParseService(botuser)
        message = make_massage("+100")
        service.recognize(message)
        message.mentions = []
        result = service.recognize(message)
        self.assertTrue(isinstance(result, parse_result.IgnorableRequest))

    def test_parse_update_command_monday(self):
        current = datetime.datetime(2020, 4, 6, 11, 30, 0)
        testcases = ["月am 100", "100 月am"]
        for command in testcases:
            result = parse.parse_update_command(command, current)
            self.assertEqual(result, parse_result.UpdateRequest("月AM", 100))

    def test_parse_update_command_sunday(self):
        current = datetime.datetime(2020, 4, 5, 10, 30, 0)
        testcases = ["買い 100", "100"]
        for command in testcases:
            result = parse.parse_update_command(command, current)
            self.assertEqual(result, parse_result.UpdateRequest("買値", 100))


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
