from dataclasses import dataclass


class ParseResult:
    pass


@dataclass
class UpdateRequest(ParseResult):
    term: str
    price: int


@dataclass
class HistoryRequest(ParseResult):
    pass


@dataclass
class InvalidUpdateRequest(ParseResult):
    pass


@dataclass
class BindRequest(ParseResult):
    name: str


class WhoAmIRequest(ParseResult):
    pass


@dataclass
class SimplePostRequest(ParseResult):
    content: str


@dataclass
class IgnorableRequest(ParseResult):
    reason: str


@dataclass
class EmptyRequest(ParseResult):
    pass


@dataclass
class EchoRequest(ParseResult):
    content: str


@dataclass
class UnknownRequest(ParseResult):
    pass
