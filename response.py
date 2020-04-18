from dataclasses import dataclass
from typing import Optional, Mapping, Iterable, Tuple

import discord


@dataclass
class Response:
    content: Optional[str]
    embed: Optional[discord.Embed]


def plain(content: str) -> Response:
    return Response(content=content, embed=None)


def success(
    title: Optional[str] = None,
    description: Optional[str] = None,
    fields: Optional[Iterable[Tuple[str, str]]] = None,
) -> Response:
    return _create_response_with_color(
        title, description, fields, discord.Color.green()
    )


def warning(
    title: Optional[str] = None,
    description: Optional[str] = None,
    fields: Optional[Iterable[Tuple[str, str]]] = None,
) -> Response:
    return _create_response_with_color(
        title, description, fields, discord.Color.orange()
    )


def error(
    title: Optional[str] = None,
    description: Optional[str] = None,
    fields: Optional[Iterable[Tuple[str, str]]] = None,
) -> Response:
    return _create_response_with_color(title, description, fields, discord.Color.red())


def _create_response_with_color(
    title: Optional[str],
    description: Optional[str],
    fields: Optional[Iterable[Tuple[str, str]]],
    color: discord.Color,
) -> Response:
    embed = discord.Embed(title=title, description=description, color=color,)
    if fields is not None:
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=True)
    return Response(content=None, embed=embed)
