import os
import dotenv
import lark_oapi as lark
from src.prompt import SYSTEM_PROMPT
from src.agent import build_agent
from src.feishu import build_feishu_client
from src.messages.handler import (
    build_event_handler,
    build_p2p_text_message_handler,
)

dotenv.load_dotenv()

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "")
FEISHU_ENCRYPT_KEY = os.getenv("FEISHU_ENCRYPT_KEY", "")

def run() -> None:
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        raise ValueError("FEISHU_APP_ID and FEISHU_APP_SECRET are required")

    agent = build_agent(
        
        system_prompt=SYSTEM_PROMPT,
    )
    feishu_client = build_feishu_client(app_id=FEISHU_APP_ID, app_secret=FEISHU_APP_SECRET)
    message_handler = build_p2p_text_message_handler(agent=agent, feishu_client=feishu_client)
    event_handler = build_event_handler(
        verification_token=FEISHU_VERIFICATION_TOKEN,
        encrypt_key=FEISHU_ENCRYPT_KEY,
        p2p_text_message_handler=message_handler,
    )

    cli = lark.ws.Client(
        FEISHU_APP_ID,
        FEISHU_APP_SECRET,
        event_handler=event_handler,
        log_level=lark.LogLevel.INFO,
    )
    cli.start()


def main() -> None:
    run()


if __name__ == "__main__":
    #  python main.py
    main()
