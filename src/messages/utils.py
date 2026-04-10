import json
from collections.abc import Mapping


def as_mapping(value: object) -> Mapping[str, object] | None:
    if isinstance(value, Mapping):
        return value
    return None


def extract_text_message(event: Mapping[str, object]) -> tuple[str,str,str] | None:

    header = as_mapping(event.get("header"))
    if header is None:
        return None
    
    event_id = header.get("event_id")
    if not isinstance(event_id, str) or not event_id:
        return None

    inner_event = as_mapping(event.get("event"))
    if inner_event is None:
        return None

    sender = as_mapping(inner_event.get("sender"))
    if sender is None:
        return None

    sender_type = sender.get("sender_type")
    if sender_type != "user":
        return None

    sender_id = as_mapping(sender.get("sender_id"))
    if sender_id is None:
        return None

    open_id_obj = sender_id.get("open_id")
    if not isinstance(open_id_obj, str) or not open_id_obj:
        return None


    message = as_mapping(inner_event.get("message"))
    if message is None:
        return None

    message_type = message.get("message_type")
    if message_type != "text":
        return None

    content_obj = message.get("content")
    if not isinstance(content_obj, str) or not content_obj:
        return None

    try:
        content_json = json.loads(content_obj)
    except json.JSONDecodeError:
        return None

    if not isinstance(content_json, dict):
        return None

    text_obj = content_json.get("text")
    if not isinstance(text_obj, str):
        return None

    text = text_obj.strip()
    if not text:
        return None
    

    return open_id_obj,event_id,text
