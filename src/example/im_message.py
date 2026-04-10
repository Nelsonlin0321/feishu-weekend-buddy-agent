from src.types.message import ImMessageReceiveV1

im_message:ImMessageReceiveV1 = {
    "schema": "2.0",
    "header": {
        "event_id": "901c05a38106965445e3bd671cdb2cc9",
        "token": "",
        "create_time": "1775831425720",
        "event_type": "im.message.receive_v1",
        "tenant_key": "1abc88bc381f1b90",
        "app_id": "cli_a953bd3b98399bd4"
    },
    "event": {
        "sender": {
            "sender_id": {
                "open_id": "ou_35167dc824c2061c13c2d4e6bd1b0ce7",
                "union_id": "on_9ba42ff6acd58a2f1f1cfe46913ec781"
            },
            "sender_type": "user",
            "tenant_key": "1abc88bc381f1b90"
        },
        "message": {
            "message_id": "om_x100b52a4d6d9acb4b31b1b36d4652b9",
            "create_time": "1775831425389",
            "update_time": "1775831425389",
            "chat_id": "oc_cf75d2ae5911f9dd566cbb2f22132936",
            "chat_type": "p2p",
            "message_type": "text",
            "content": "{\"text\":\"Hi\"}"
        }
    }
}