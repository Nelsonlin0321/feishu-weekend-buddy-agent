import json
from loguru import logger
from collections.abc import Callable
from uuid import uuid4
import lark_oapi as lark
from langchain_core.runnables import Runnable, RunnableConfig

from lark_oapi.api.im.v1 import (
    CreateMessageRequest,
    CreateMessageRequestBody,
    CreateMessageResponse,
)

from src.messages.utils import as_mapping, extract_text_message
from src.feishu import build_feishu_client
from src.middlewares import FeishuRuntimeContext

EVENT_ID_SET = set()

def send_text_message(*, client: lark.Client, open_id: str, text: str) -> CreateMessageResponse:
    request: CreateMessageRequest = (
        CreateMessageRequest.builder()
        .receive_id_type("open_id")
        .request_body(
            CreateMessageRequestBody.builder()
            .receive_id(open_id)
            .msg_type("text")
            .content(json.dumps({"text": text}, ensure_ascii=False))
            .uuid(str(uuid4()))
            .build()
        )
        .build()
    )
    im = client.im
    if im is None:
        raise RuntimeError("Feishu IM API is not available on this client")
    v1 = im.v1
    if v1 is None:
        raise RuntimeError("Feishu IM v1 API is not available on this client")
    message = v1.message
    if message is None:
        raise RuntimeError("Feishu IM message API is not available on this client")
    return message.create(request)




def build_p2p_text_message_handler(
    *,
    agent: Runnable,
    feishu_client: lark.Client,
    history_to_load: int = 20,
) -> Callable[[lark.im.v1.P2ImMessageReceiveV1], None]:
    def do_p2_im_message_receive_v1(data: lark.im.v1.P2ImMessageReceiveV1) -> None:
        try:
            payload_str = lark.JSON.marshal(data)
            if payload_str is None:
                return
            payload_obj = json.loads(payload_str)
        except (TypeError, json.JSONDecodeError):
            return

        payload = as_mapping(payload_obj)
        if payload is None:
            return

        extracted = extract_text_message(payload)
        if extracted is None:
            return

        open_id,event_id, user_text = extracted
        if event_id in EVENT_ID_SET:
            logger.info(f"Duplicate event_id: {event_id}")
            return
        EVENT_ID_SET.add(event_id)

        config: RunnableConfig = {
            "configurable": {"thread_id": f"feishu:{open_id}"},
            "recursion_limit": 10,
        }
        context = FeishuRuntimeContext(open_id=open_id, history_to_load=history_to_load)
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_text}]},
            config=config,
            context=context,
        )
        reply_obj = result["messages"][-1].content
        reply = reply_obj if isinstance(reply_obj, str) else str(reply_obj)
        send_text_message(client=feishu_client, open_id=open_id, text=reply)

    return do_p2_im_message_receive_v1


def build_event_handler(
    *,
    verification_token: str,
    encrypt_key: str,
    p2p_text_message_handler: Callable[[lark.im.v1.P2ImMessageReceiveV1], None],
) -> lark.EventDispatcherHandler:
    return (
        lark.EventDispatcherHandler.builder(verification_token, encrypt_key)
        .register_p2_im_message_receive_v1(p2p_text_message_handler)
        .build()
    )


__all__ = [
    "build_event_handler",
    "build_p2p_text_message_handler",
    "build_feishu_client",
    "send_text_message",
]
