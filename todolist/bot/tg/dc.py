from dataclasses import field
from typing import List, Optional, ClassVar, Type

from marshmallow import EXCLUDE, Schema
from marshmallow_dataclass import dataclass

"""
List of API used:
    MessageFrom (User): https://core.telegram.org/bots/api#user
    Chat: https://core.telegram.org/bots/api#chat
    Message: https://core.telegram.org/bots/api#message
    UpdateObj (Update): https://core.telegram.org/bots/api#update
    GetUpdateResponse (getUpdates): https://core.telegram.org/bots/api#getupdates
    SendMessageResponse (sendMessage): https://core.telegram.org/bots/api#sendmessage
"""


@dataclass
class MessageFrom:
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str]
    username: Optional[str]

    class Meta:
        unknown = EXCLUDE


@dataclass
class Chat:
    id: int
    type: str
    title: Optional[str]
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]

    class Meta:
        unknown = EXCLUDE


@dataclass
class Message:
    message_id: int
    from_: MessageFrom = field(metadata={'data_key': 'from'})
    chat: Chat
    text: Optional[str] = None

    class Meta:
        unknown = EXCLUDE


@dataclass
class UpdateObj:
    update_id: int
    message: Message

    class Meta:
        unknown = EXCLUDE


@dataclass
class GetUpdatesResponse:
    ok: bool
    result: List[UpdateObj]

    Schema = Schema

    class Meta:
        unknown = EXCLUDE


@dataclass
class SendMessageResponse:
    ok: bool
    result: Message

    Schema = Schema

    class Meta:
        unknown = EXCLUDE
