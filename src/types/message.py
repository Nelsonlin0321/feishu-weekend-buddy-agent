from typing import Literal, TypedDict


class ImMessageHeader(TypedDict):
    event_id: str
    token: str
    create_time: str
    event_type: Literal["im.message.receive_v1"]
    tenant_key: str
    app_id: str


class ImMessageSenderId(TypedDict):
    open_id: str
    union_id: str


class ImMessageSender(TypedDict):
    sender_id: ImMessageSenderId
    sender_type: Literal["user"]
    tenant_key: str


class ImMessageMessage(TypedDict):
    message_id: str
    create_time: str
    update_time: str
    chat_id: str
    chat_type: Literal["p2p"]
    message_type: Literal["text"]
    content: str


class ImMessageEvent(TypedDict):
    sender: ImMessageSender
    message: ImMessageMessage


class ImMessageReceiveV1(TypedDict):
    schema: Literal["2.0"]
    header: ImMessageHeader
    event: ImMessageEvent

__all__ = ["ImMessageReceiveV1"]