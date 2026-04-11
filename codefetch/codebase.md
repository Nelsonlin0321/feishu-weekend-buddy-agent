<filetree>
Project Structure:
├── src
│   ├── example
│   ├── messages
│   ├── middlewares
│   ├── tools
│   ├── types
│   ├── agent.py
│   ├── feishu.py
│   ├── model.py
│   ├── prompt.py
│   └── utils.py
├── test
│   ├── __init__.py
│   ├── test_event_subscription.py
│   └── test_send_message.py
├── .python-version
├── AGENTS.md
├── main.py
└── pyproject.toml

</filetree>

<source_code>
.python-version
```
3.12
```

AGENTS.md
```

## Agent Buddy Design and Implementation

### Background & Goal: 
I want to launch a product for users. I call the project to be Feishu AI Weekend Buddy Agent. 
The goal of the product is to helps a user navigate the entire social friction loop: 
For example: “I want to do something this weekend people.”

### Technical & Product RequirementsA. Core Interaction (Feishu)
A. Core Interaction (Feishu)
The primary interface must be within Feishu. The agent should:
- Capture Intent: Understand preferences (activity, availability, location, budget, group vibe).
- Execute Logic: Suggest activities, explain the "why" behind recommendations, and propose
suit buddy types.
- Drive Action: Draft invite messages or coordination cards to move the user toward a firm
confirmation.

B. Implementation Specs
- Real Integration: Use real Feishu components (Bots, Message Cards, Group Invites, or Event
Cards). Avoid using only mock screens.

- Web Context (Optional/Supporting): You may use a lightweight web dashboard to show
broader context (e.g., activity history, user trends, or recommendation insights).

C. Optional Extensions
Feel free to extend the demo in any direction that showcases your strengths:
Advanced agent reasoning/planning.
Multi-step coordination or memory/preference learning.
Unique agent-tool usage or new interaction patterns.

3. Constraints & Expectations
C. Optional Extensions
Feel free to extend the demo in any direction that showcases your strengths:
- Advanced agent reasoning/planning.
- Multi-step coordination or memory/preference learning.
- Unique agent-tool usage or new interaction patterns.

### Tech Stack:
 - Agent Framework: Langchain, OpenAI
 - Database: sqlite
 - ORM: MongoDB
 - Web Framework: FastAPI
 - Python Package Manager: uv
 - Feishu Integration: Feishu  SDK
```

main.py
```
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
```

pyproject.toml
```
[project]
name = "feishu-weekend-buddy-agent"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "langchain>=1.0.7",
    "langchain-deepseek>=1.0.1",
    "langchain-openai==1.1.6",
    "langgraph==1.0.5",
    "langgraph-prebuilt==1.0.5",
    "lark-oapi>=1.5.3",
    "loguru>=0.7.3",
    "openai==2.14.0",
    "python-dotenv>=1.2.2",
    "python-socks>=2.8.1",
]

[dependency-groups]
dev = [
    "jupyter>=1.1.1",
]
```

src/agent.py
```
import os
from pathlib import Path
from pydantic import SecretStr
from langchain_core.runnables import Runnable
from langchain.agents import create_agent
from src.model import build_model
from src.types.context import FeishuRuntimeContext
from src.middlewares import  LoadHistoryMiddleware, SaveHistoryMiddleware
from src.tools.knowledge import build_knowledge_tools


DEEPINFRA_API_KEY =  SecretStr(os.getenv("DEEPINFRA_API_KEY",""))


def build_agent(
    system_prompt: str,
    *,
    memory_base_dir: str = "./.memory",
    default_history_to_load: int = 20,
) -> Runnable:
    model = build_model()
    base_dir = Path(memory_base_dir).expanduser().resolve()
    tools = build_knowledge_tools(base_dir=base_dir)
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        context_schema=FeishuRuntimeContext,
        middleware=[
            LoadHistoryMiddleware(base_dir=base_dir, default_history_to_load=default_history_to_load),
            SaveHistoryMiddleware(base_dir=base_dir),
        ],
    )

if __name__ == "__main__":

    #  python -m src.agent
    from langchain_core.messages import HumanMessage
    start_messages = [HumanMessage(content="Hi")]
    agent = build_agent("You are a helpful assistant.")
    response = agent.invoke({"messages": start_messages})
    print(response)
```

src/feishu.py
```
import lark_oapi as lark


def build_feishu_client(*, app_id: str, app_secret: str) -> lark.Client:
    return (
        lark.Client.builder()
        .app_id(app_id)
        .app_secret(app_secret)
        .log_level(lark.LogLevel.INFO)
        .build()
    )


__all__ = ["build_feishu_client"]
```

src/model.py
```
import dotenv
from src.utils import get_env
from pydantic import SecretStr
from langchain_deepseek import ChatDeepSeek
dotenv.load_dotenv()
AI_GATEWAY_API_KEY = SecretStr(get_env("AI_GATEWAY_API_KEY"))


def build_model(
    model_name: str="minimax/minimax-m2.5",
    reasoning: bool = True,
):
    llm = ChatDeepSeek(
        api_key=AI_GATEWAY_API_KEY,
        api_base="https://ai-gateway.vercel.sh/v1",
        model=model_name,
        extra_body={"reasoning": {"enabled": reasoning}},
    )
    return llm


__all__ = [
    "build_model",
]

if __name__ == "__main__":
    # python -m src.models
    model = build_model()
    print(model.invoke("Hello"))
```

src/prompt.py
```
from datetime import datetime

SYSTEM_PROMPT = f"""You are Feishu AI Weekend Buddy Agent.

Today: {datetime.now().astimezone().strftime("%Y-%m-%d (%A)")}

Goal: help the user navigate the full social friction loop for weekend plans:
- Capture intent (activity type, time, location, budget, group vibe)
- Recommend options with clear "why"
- Drive action by drafting invite/coordination messages

Guidelines:
- Prefer tool usage for memory:
  - When you learn stable user info (preferences/constraints/availability/people/places), call knowledge_write with kind="document".
    Use mode="upsert" to append updates over time, or mode="replace" to overwrite.
  - When logging what happened (plans/outcomes/recaps), call knowledge_write with kind="event".
  - Before choosing a category/name, call knowledge_tree to reuse existing categories and avoid duplicates.
  - Always use a clear, specific name to keep files easy to search and scan later. Prefer patterns like:
    - "{{person_or_group}}: {{topic}} ({{key_constraints_or_prefs}})"
    - "{{place_or_area}}: {{topic}} ({{budget_or_time_window}})"
    - "{{date_or_weekend}}: {{plan_or_recap}} ({{who}}/{{where}})"
    Avoid vague names like "notes", "plan", "preferences" without details.
  - When you need to recall saved info, call knowledge_tree to find the correct rel_path, then call knowledge_read(rel_path).
- If key info is missing, ask up to 3 concise questions.
- Provide 3-5 concrete suggestions (not generic), with quick rationale.
- End with an action step (e.g., “Want me to draft an invite?”).
"""
```

src/utils.py
```
import os
def get_env(name: str, default="") -> str:
    value = os.environ.get(name)
    if not value and default == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value or default
```

test/__init__.py
```
```

test/test_event_subscription.py
```
import os
import lark_oapi as lark
import dotenv
dotenv.load_dotenv()

FEISHU_APP_ID=os.getenv("FEISHU_APP_ID","")
FEISHU_APP_SECRET=os.getenv("FEISHU_APP_SECRET","")

if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
    raise ValueError("FEISHU_APP_ID and FEISHU_APP_SECRET are required")


def do_p2_im_message_receive_v1(data: lark.im.v1.P2ImMessageReceiveV1) -> None:
    print(f'[ do_p2_im_message_receive_v1 access ], data: {lark.JSON.marshal(data, indent=4)}')
def do_message_event(data: lark.CustomizedEvent) -> None:
    print(f'[ do_customized_event access ], type: message, data: {lark.JSON.marshal(data, indent=4)}')



event_handler = lark.EventDispatcherHandler.builder("", "") \
    .register_p2_im_message_receive_v1(do_p2_im_message_receive_v1) \
    .register_p1_customized_event("这里填入你要自定义订阅的 event 的 key，例如 out_approval", do_message_event) \
    .build()


    
def main():
    cli = lark.ws.Client(FEISHU_APP_ID, FEISHU_APP_SECRET,
                         event_handler=event_handler,
                         log_level=lark.LogLevel.DEBUG)
    cli.start()
if __name__ == "__main__":
    main()
    # python -m test.test_event_subscription
    # print("Hello from feishu-weekend-buddy-agent!")
```

test/test_send_message.py
```
import os
import dotenv
import asyncio
import json
from uuid import uuid4
import lark_oapi as lark
from lark_oapi.api.im.v1 import CreateMessageRequest,CreateMessageRequestBody,CreateMessageResponse

dotenv.load_dotenv()

FEISHU_APP_ID=os.getenv("FEISHU_APP_ID","")
FEISHU_APP_SECRET=os.getenv("FEISHU_APP_SECRET","")
if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
    raise ValueError("FEISHU_APP_ID and FEISHU_APP_SECRET are required")

async def main():
    client = lark.Client.builder() \
        .app_id(FEISHU_APP_ID) \
        .app_secret(FEISHU_APP_SECRET) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    uuid = str(uuid4())
    request: CreateMessageRequest = CreateMessageRequest.builder() \
        .receive_id_type("open_id") \
        .request_body(CreateMessageRequestBody.builder()
            .receive_id("ou_35167dc824c2061c13c2d4e6bd1b0ce7")
            .msg_type("text")
            .content("{\"text\":\"test content\"}")
            .uuid(uuid)
            .build()) \
        .build()

    # 发起请求
    response: CreateMessageResponse = await client.im.v1.message.acreate(request) # # pyright: ignore [reportOptionalMemberAccess]

    # 处理失败返回
    # if not response.success():
    #     lark.logger.error(
    #         f"client.im.v1.message.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
    #     return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))


if __name__ == "__main__":
    # python -m test.test_send_message
    asyncio.run(main()) # 异步方式
```

src/example/im_message.py
```
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
```

src/messages/handler.py
```
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
        # result = agent.invoke(
        #     {"messages": [{"role": "user", "content": user_text}]},
        #     config=config,
        #     context=context,
        # )
        # reply_obj = result["messages"][-1].content

        events = agent.stream(
            {"messages": [{"role": "user", "content": user_text}]},
            context=context,
        )
        content:str=""
        for event in events:
            if "model" in event:
                if "messages" in event["model"]:
                    message = event["model"]["messages"][-1]
                    message.pretty_print()
                    content = message.content

        reply = content
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
```

src/messages/utils.py
```
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
```

src/middlewares/__init__.py
```
from src.middlewares.load_history_middleware import LoadHistoryMiddleware
from src.middlewares.save_history_middleware import SaveHistoryMiddleware
from src.types.context import FeishuRuntimeContext

__all__ = ["FeishuRuntimeContext", "LoadHistoryMiddleware", "SaveHistoryMiddleware"]
```

src/middlewares/history_storage.py
```
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


Role = Literal["user", "bot"]


@dataclass(frozen=True, slots=True)
class StoredMessage:
    role: Role
    content: object
    timestamp: str
    path: Path


_OPEN_ID_SAFE = re.compile(r"[^a-zA-Z0-9_\-]")


def sanitize_open_id(open_id: str) -> str:
    return _OPEN_ID_SAFE.sub("_", open_id).strip("_") or "unknown"


def now_timestamp() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S")


def messages_dir(*, base_dir: Path, open_id: str) -> Path:
    return base_dir / sanitize_open_id(open_id) / "messages"


def message_path(*, base_dir: Path, open_id: str, role: Role, timestamp: str) -> Path:
    prefix = "user" if role == "user" else "bot"
    return messages_dir(base_dir=base_dir, open_id=open_id) / f"{prefix}_{timestamp}"


def _coerce_jsonable(value: object) -> object:
    try:
        json.dumps(value, ensure_ascii=False)
        return value
    except (TypeError, ValueError):
        return str(value)


def write_message(
    *,
    base_dir: Path,
    open_id: str,
    role: Role,
    content: object,
    timestamp: str | None = None,
) -> Path:
    ts = timestamp or now_timestamp()
    path = message_path(base_dir=base_dir, open_id=open_id, role=role, timestamp=ts)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"role": role, "content": _coerce_jsonable(content), "timestamp": ts}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _infer_role_from_filename(name: str) -> Role | None:
    if name.startswith("user_"):
        return "user"
    if name.startswith("bot_"):
        return "bot"
    return None


def _infer_timestamp_from_filename(name: str) -> str | None:
    if name.startswith("user_"):
        return name[len("user_") :]
    if name.startswith("bot_"):
        return name[len("bot_") :]
    return None


def read_recent_messages(*, base_dir: Path, open_id: str, limit: int) -> list[StoredMessage]:
    if limit <= 0:
        return []

    directory = messages_dir(base_dir=base_dir, open_id=open_id)
    if not directory.exists() or not directory.is_dir():
        return []

    candidates: list[Path] = []
    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        if _infer_role_from_filename(entry.name) is None:
            continue
        candidates.append(entry)

    candidates.sort(key=lambda p: p.name)
    selected = candidates[-limit:]

    results: list[StoredMessage] = []
    for path in selected:
        raw = path.read_text(encoding="utf-8")
        role = _infer_role_from_filename(path.name) or "user"
        timestamp = _infer_timestamp_from_filename(path.name) or ""
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                parsed_role = obj.get("role")
                if parsed_role in ("user", "bot"):
                    role = parsed_role
                parsed_ts = obj.get("timestamp")
                if isinstance(parsed_ts, str) and parsed_ts:
                    timestamp = parsed_ts
                content = obj.get("content", "")
                results.append(StoredMessage(role=role, content=content, timestamp=timestamp, path=path))
                continue
        except (TypeError, json.JSONDecodeError, ValueError):
            pass

        results.append(StoredMessage(role=role, content=raw, timestamp=timestamp, path=path))

    return results

```

src/middlewares/load_history_middleware.py
```
from __future__ import annotations

import json
from pathlib import Path

from langchain.agents.middleware.types import AgentMiddleware, AgentState
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime

from src.middlewares.history_storage import read_recent_messages
from src.types.context import FeishuRuntimeContext


def _content_for_message(value: object) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)


def _open_id_from_runtime(runtime: Runtime[FeishuRuntimeContext]) -> str | None:
    context = runtime.context
    if context is None:
        return None
    if isinstance(context, FeishuRuntimeContext):
        return context.open_id
    open_id = getattr(context, "open_id", None)
    return open_id if isinstance(open_id, str) and open_id else None


def _history_to_load_from_runtime(
    runtime: Runtime[FeishuRuntimeContext], default: int
) -> int:
    context = runtime.context
    if context is None:
        return default
    if isinstance(context, FeishuRuntimeContext):
        return context.history_to_load
    raw = getattr(context, "history_to_load", None)
    if isinstance(raw, int):
        return raw
    return default


class LoadHistoryMiddleware(AgentMiddleware[AgentState[object], FeishuRuntimeContext]):
    def __init__(self, *, base_dir: Path, default_history_to_load: int = 20) -> None:
        self._base_dir = base_dir
        self._default_history_to_load = default_history_to_load

    def before_agent(
        self, state: AgentState[object], runtime: Runtime[FeishuRuntimeContext]
    ) -> dict[str, object] | None:
        open_id = _open_id_from_runtime(runtime)
        if open_id is None:
            return None

        limit = _history_to_load_from_runtime(runtime, self._default_history_to_load)
        stored = read_recent_messages(base_dir=self._base_dir, open_id=open_id, limit=limit)
        if not stored:
            return None

        history_messages = [
            HumanMessage(content=_content_for_message(m.content))
            if m.role == "user"
            else AIMessage(content=_content_for_message(m.content))
            for m in stored
        ]

        current_messages = list(state.get("messages", []))
        new_messages = [*history_messages, *current_messages]

        return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *new_messages]}
```

src/middlewares/save_history_middleware.py
```
from __future__ import annotations

from pathlib import Path

from langchain.agents.middleware.types import AgentMiddleware, AgentState
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.runtime import Runtime

from src.middlewares.history_storage import write_message
from src.types.context import FeishuRuntimeContext


def _open_id_from_runtime(runtime: Runtime[FeishuRuntimeContext]) -> str | None:
    context = runtime.context
    if context is None:
        return None
    if isinstance(context, FeishuRuntimeContext):
        return context.open_id
    open_id = getattr(context, "open_id", None)
    return open_id if isinstance(open_id, str) and open_id else None


class SaveHistoryMiddleware(AgentMiddleware[AgentState[object], FeishuRuntimeContext]):
    def __init__(self, *, base_dir: Path) -> None:
        self._base_dir = base_dir

    def before_agent(
        self, state: AgentState[object], runtime: Runtime[FeishuRuntimeContext]
    ) -> dict[str, object] | None:
        open_id = _open_id_from_runtime(runtime)
        if open_id is None:
            return None

        messages = state.get("messages", [])
        last = messages[-1] if messages else None
        if isinstance(last, HumanMessage):
            write_message(
                base_dir=self._base_dir,
                open_id=open_id,
                role="user",
                content=last.content,
            )
        return None

    def after_agent(
        self, state: AgentState[object], runtime: Runtime[FeishuRuntimeContext]
    ) -> dict[str, object] | None:
        open_id = _open_id_from_runtime(runtime)
        if open_id is None:
            return None

        messages = state.get("messages", [])
        last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
        if isinstance(last_ai, AIMessage):
            write_message(
                base_dir=self._base_dir,
                open_id=open_id,
                role="bot",
                content=last_ai.content,
            )
        return None
```

src/tools/knowledge.py
```
from pathlib import Path
from src.tools.knowledge_paths import _safe_knowledge_path, knowledge_dir, safe_knowledge_path, slugify
from src.tools.knowledge_records import list_knowledge_tree, read_knowledge_record, write_knowledge_record
from src.tools.knowledge_tools import build_knowledge_tools
from src.tools.knowledge_types import KnowledgeRecordKind, KnowledgeWriteMode

__all__ = [
    "KnowledgeRecordKind",
    "KnowledgeWriteMode",
    "_safe_knowledge_path",
    "build_knowledge_tools",
    "knowledge_dir",
    "list_knowledge_tree",
    "read_knowledge_record",
    "safe_knowledge_path",
    "slugify",
    "write_knowledge_record",
]


if __name__ == "__main__":

    base_dir = Path("./memory")
    print(base_dir.absolute())
    open_id = "ou_test_user_123"

    doc_path = write_knowledge_record(
        base_dir=base_dir,
        open_id=open_id,
        category="preferences",
        name="Alice: food likes/dislikes",
        kind="document",
        content="Likes: spicy Sichuan\nDislikes: cilantro",
        mode="replace",
    )
    assert doc_path.exists()

    doc_path_2 = write_knowledge_record(
        base_dir=base_dir,
        open_id=open_id,
        category="preferences",
        name="Alice: food likes/dislikes",
        kind="document",
        content="Also likes: hotpot",
        mode="upsert",
    )
    assert doc_path_2 == doc_path

    root = knowledge_dir(base_dir=base_dir, open_id=open_id).resolve()
    doc_rel = str(doc_path.relative_to(root))
    doc_content = read_knowledge_record(base_dir=base_dir, open_id=open_id, rel_path=doc_rel)
    assert "Likes: spicy Sichuan" in doc_content
    assert "Also likes: hotpot" in doc_content

    event_path = write_knowledge_record(
        base_dir=base_dir,
        open_id=open_id,
        category="activity_history",
        name="Weekend plan",
        kind="event",
        content="Went to a board game cafe with friends.",
        mode="replace",
    )
    assert event_path.exists()

    event_rel = str(event_path.relative_to(root))
    event_content = read_knowledge_record(base_dir=base_dir, open_id=open_id, rel_path=event_rel)
    assert "Went to a board game cafe with friends." in event_content

    print("doc_rel:", doc_rel)
    print("event_rel:", event_rel)
    print()
    print("tree:")
    print(list_knowledge_tree(base_dir=base_dir, open_id=open_id, rel_path="."))
```

src/tools/knowledge_paths.py
```
import re
from pathlib import Path

from src.middlewares.history_storage import sanitize_open_id

_SLUG_SAFE = re.compile(r"[^a-zA-Z0-9_\\-]")


def knowledge_dir(*, base_dir: Path, open_id: str) -> Path:
    return base_dir / sanitize_open_id(open_id) / "knowledge"


def slugify(value: str) -> str:
    return _SLUG_SAFE.sub("_", value.strip().lower()).strip("_") or "untitled"


def safe_knowledge_path(*, base_dir: Path, open_id: str, rel_path: str) -> Path:
    root = knowledge_dir(base_dir=base_dir, open_id=open_id)
    if not rel_path or rel_path.startswith("/"):
        raise ValueError("rel_path must be a non-empty relative path under knowledge/")

    candidate = (root / rel_path).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("rel_path must stay within knowledge/ directory")
    return candidate


_safe_knowledge_path = safe_knowledge_path
```

src/tools/knowledge_records.py
```
from datetime import datetime, timezone
from pathlib import Path

from src.tools.knowledge_paths import knowledge_dir, safe_knowledge_path, slugify
from src.tools.knowledge_types import KnowledgeRecordKind, KnowledgeWriteMode


def write_knowledge_record(
    base_dir: Path,
    open_id: str,
    category: str,
    name: str,
    kind: KnowledgeRecordKind,
    content: str,
    mode: KnowledgeWriteMode = "upsert",
) -> Path:
    category_slug = slugify(category)
    name_slug = slugify(name)
    day_and_time = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d:%H:%M:%S")
    day = day_and_time[:10]
    time = day_and_time[11:]
    if kind == "event":
        rel = f"{category_slug}/{day}/{time}_{name_slug}.md"
    else:
        rel = f"{category_slug}/{day}/{name_slug}.md"

    path = safe_knowledge_path(base_dir=base_dir, open_id=open_id, rel_path=rel)
    path.parent.mkdir(parents=True, exist_ok=True)

    body = content.strip()
    frontmatter = "\n".join(
        [
            "---",
            f"kind: {kind}",
            f"category: {category_slug}",
            f"name: {name_slug}",
            f"{day_and_time}",
            "---",
            "",
        ]
    )

    if kind == "document" and mode == "upsert" and path.exists():
        existing = path.read_text(encoding="utf-8")
        updated = "\n".join(
            [
                existing.rstrip(),
                "",
                f"## Update {day_and_time}",
                "",
                body,
                "",
            ]
        )
        path.write_text(updated, encoding="utf-8")
        return path

    markdown = "\n".join(
        [
            frontmatter,
            f"# {category_slug}: {name_slug}",
            "",
            body,
            "",
        ]
    )
    path.write_text(markdown, encoding="utf-8")
    return path


def read_knowledge_record(*, base_dir: Path, open_id: str, rel_path: str) -> str:
    path = safe_knowledge_path(base_dir=base_dir, open_id=open_id, rel_path=rel_path)
    return path.read_text(encoding="utf-8")


def list_knowledge_tree(
    *,
    base_dir: Path,
    open_id: str,
    rel_path: str = ".",
    max_depth: int = 10,
    max_entries: int = 200,
) -> str:
    root = knowledge_dir(base_dir=base_dir, open_id=open_id)
    root_resolved = root.resolve()
    start = safe_knowledge_path(base_dir=base_dir, open_id=open_id, rel_path=rel_path)
    if not start.exists():
        return f"(empty) {start.relative_to(root_resolved)} does not exist"

    lines: list[str] = [str(start.relative_to(root_resolved)) + ("/" if start.is_dir() else "")]
    count = 0

    def walk(current: Path, depth: int) -> None:
        nonlocal count
        if count >= max_entries:
            return
        if depth > max_depth:
            return
        if not current.is_dir():
            return

        entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        for entry in entries:
            if count >= max_entries:
                return
            prefix = "  " * depth
            rel = entry.relative_to(root_resolved)
            lines.append(f"{prefix}- {rel}" + ("/" if entry.is_dir() else ""))
            count += 1
            if entry.is_dir():
                walk(entry, depth + 1)

    walk(start, 1)
    if count >= max_entries:
        lines.append("... (truncated)")
    return "\n".join(lines)
```

src/tools/knowledge_tools.py
```
from pathlib import Path
import shutil
from typing import cast,Literal

from langchain.tools import ToolRuntime, tool
from langchain_core.tools import BaseTool
from loguru import logger

from src.middlewares.history_storage import sanitize_open_id
from src.tools.knowledge_paths import knowledge_dir, safe_knowledge_path, slugify
from src.tools.knowledge_records import list_knowledge_tree, read_knowledge_record, write_knowledge_record
from src.types.context import FeishuRuntimeContext


def build_knowledge_tools(*, base_dir: Path) -> list[BaseTool]:
    @tool("knowledge_write")
    def knowledge_write(
        category: str,
        name: str,
        content: str,
        runtime: ToolRuntime[FeishuRuntimeContext],
        kind: Literal["document", "event"] = "event",
        mode: Literal["replace", "upsert"]='replace',
    ) -> str:
        """
        Persist user-specific knowledge to the your local memory

        Use this tool when you learn something that should be remembered across turns/sessions, such as:
        preferences (food, activities), constraints (budget, time window), availability, locations, people/group vibe,
        or an activity log of what happened on a specific day. Before calling this tool, check the knowledge tree to avoid duplicates.

        How it’s organized:
        - Stored as markdown files, grouped by category (folder) and a slugified name.
        - kind="document": stable file at {category}/YYYY-MM-DD/{name}.md (good for profile/preferences you update over time).
        - kind="event": timestamped file at {category}/YYYY-MM-DD/HH:MM:SS_{name}.md (good for logs/history).

        Args:
            category: A consistent bucket name. Examples: "profile", "preferences", "availability",
                "constraints", "people", "places", "budgets", "activity_history", "conversation_notes", etc
                You can create a new category if your knowledge is not fit in any existing category to capture the any user intent.
                In order to make the category consistent, you may have to read the knowledge tree first. 
            name: A descriptive title that makes the file easy to find later. Examples:
                "Alice: food likes/dislikes", "Weekend availability", "Budget constraints", "Last weekend recap".
            content: Markdown body to store. Prefer concrete, structured bullets. Avoid secrets (tokens, passwords).
            kind: "document" or "event". Defaults to "event" in this tool signature.
            mode: For kind="document", controls how updates are written:
                - "replace": overwrite the file content
                - "upsert": append a dated "Update ..." section if the file already exists
                For kind="event", the file is always a new timestamped record. Defaults to "replace" here.

        Returns:
            A confirmation string including the relative path written under the user’s knowledge directory.

        Recommended usage patterns:
        - Long-lived memory (profile/preferences): kind="document" + mode="upsert"
        - Single-shot snapshot (constraints right now): kind="document" + mode="replace"
        - Activity log / what happened: kind="event"
        """
        ctx = runtime.context
        open_id = ctx.open_id
        open_id_safe = sanitize_open_id(open_id)
        path = write_knowledge_record(
            base_dir=base_dir,
            open_id=open_id,
            category=category,
            name=name,
            kind="event" if kind == "event" else "document",
            mode="replace" if mode == "replace" else "upsert",
            content=content,
        )
        root = knowledge_dir(base_dir=base_dir, open_id=open_id)
        rel_path = path.relative_to(root)
        logger.debug(
            "knowledge_write success open_id={} rel_path={} bytes={}",
            open_id_safe,
            str(rel_path),
            path.stat().st_size,
        )
        return f"Written to {rel_path} successfully"

    @tool("knowledge_read")
    def knowledge_read(rel_path: str, runtime: ToolRuntime[FeishuRuntimeContext]) -> str:
        """
        Read previously stored knowledge

        Use this tool when you need to recall details that were saved with knowledge_write, such as preferences,
        constraints, availability, or past activity logs.

        Args:
            rel_path: File path relative to the user’s knowledge root. Example:
                - "preferences/alice__food_likes_dislikes.md"
                - "activity_history/2026-04-10/23:15:43_weekend_plan.md"
                Prefer getting valid paths by calling the knowledge_tree tool first.

        Returns:
            The full markdown content of the file.
        """
        ctx = runtime.context
        open_id_safe = sanitize_open_id(ctx.open_id)
        logger.debug("knowledge_read called open_id={} rel_path={}", open_id_safe, rel_path)
        content = read_knowledge_record(base_dir=base_dir, open_id=ctx.open_id, rel_path=rel_path)
        return content

    @tool("knowledge_rename")
    def knowledge_rename(
        src_rel_path: str,
        dst_rel_path: str,
        runtime: ToolRuntime[FeishuRuntimeContext],
        overwrite: bool = False,
    ) -> str:
        """
        Rename or move a stored knowledge file/folder.

        Use this tool when you want to:
        - Fix a category folder name
        - Re-organize stored knowledge
        - Rename a single file to a better title

        Args:
            src_rel_path: Source path relative to the user’s knowledge root.
                Prefer getting valid paths by calling knowledge_tree first.
            dst_rel_path: Destination path relative to the user’s knowledge root.
                If dst_rel_path points to an existing directory, the source will be moved into it.
            overwrite: If true, replace an existing destination file/folder. Default false.

        Returns:
            A confirmation string including the final destination relative path.
        """
        ctx = runtime.context
        open_id = ctx.open_id
        open_id_safe = sanitize_open_id(open_id)

        root = knowledge_dir(base_dir=base_dir, open_id=open_id).resolve()
        src = safe_knowledge_path(base_dir=base_dir, open_id=open_id, rel_path=src_rel_path)
        dst = safe_knowledge_path(base_dir=base_dir, open_id=open_id, rel_path=dst_rel_path)

        if src.resolve() == root:
            raise ValueError("src_rel_path cannot be the knowledge root")
        if dst.resolve() == root:
            raise ValueError("dst_rel_path cannot be the knowledge root")
        if not src.exists():
            raise FileNotFoundError(f"Source does not exist: {src_rel_path}")

        final_dst = dst
        if dst.exists() and dst.is_dir():
            final_dst = dst / src.name

        if final_dst.exists():
            if not overwrite:
                rel_final = str(final_dst.relative_to(root))
                raise FileExistsError(f"Destination already exists: {rel_final}")
            if final_dst.is_dir():
                shutil.rmtree(final_dst)
            else:
                final_dst.unlink()

        final_dst.parent.mkdir(parents=True, exist_ok=True)
        moved_to = Path(shutil.move(str(src), str(final_dst))).resolve()
        rel_moved = moved_to.relative_to(root)
        logger.debug(
            "knowledge_rename success open_id={} src={} dst={}",
            open_id_safe,
            src_rel_path,
            str(rel_moved),
        )
        return f"Renamed to {rel_moved} successfully"

    @tool("knowledge_tree")
    def knowledge_tree(
        runtime: ToolRuntime[FeishuRuntimeContext],
        rel_path: str = ".",
        max_depth: int = 10,
        max_entries: int = 500,
    ) -> str:
        """
        List the current user’s knowledge folder as a readable tree (paths under /memory/{open_id}/knowledge).

        Use this tool to:
        - Discover what the agent has already saved for the user (categories and files).
        - Get the exact rel_path values to pass into knowledge_read.
        - Keep category naming consistent before writing new records with knowledge_write.

        Args:
            rel_path: Starting folder (relative to the user’s knowledge root). Defaults to "." (the root).
                Examples:
                - "." (everything)
                - "preferences"
                - "activity_history/2026-04-10"
            max_depth: How many nested directory levels to include.
            max_entries: Maximum number of lines/entries to return (output will truncate beyond this).

        Returns:
            A newline-separated tree. Directories end with "/". Each file line shows the rel_path you can reuse
            in knowledge_read.
        """
        open_id = runtime.context.open_id
        open_id_safe = sanitize_open_id(open_id)
        logger.debug(
            "knowledge_tree called open_id={} rel_path={} max_depth={} max_entries={}",
            open_id_safe,
            rel_path,
            max_depth,
            max_entries,
        )
        try:
            tree = list_knowledge_tree(
                base_dir=base_dir,
                open_id=open_id,
                rel_path=rel_path,
                max_depth=max_depth,
                max_entries=max_entries,
            )
        except Exception:
            logger.exception(
                "knowledge_tree failed open_id={} rel_path={} max_depth={} max_entries={}",
                open_id_safe,
                rel_path,
                max_depth,
                max_entries,
            )
            raise

        logger.debug("knowledge_tree success open_id={} lines={}", open_id_safe, tree.count("\n") + 1 if tree else 0)
        return tree

    @tool("invite_send_mock")
    def invite_send_mock(
        to_open_id: str,
        text: str,
        runtime: ToolRuntime[FeishuRuntimeContext],
        purpose: Literal["invite", "reminder", "confirmation"] = "invite",
        title: str = "",
    ) -> str:
        """
        Sending an invite message to someone (no real Feishu API call).

        Use this tool to outbound coordination messages. It logs the "sent"
        invite into the user's local knowledge store as an event record.

        Args:
            to_open_id: Recipient's Feishu open_id, ask the user to provide this.
            text: Message content you would send.
            purpose: Message type. One of: "invite", "reminder", "confirmation".
            title: Optional short label to help later browsing/searching.

        Returns:
            A confirmation string including the relative path where the invite was logged.
        """
        ctx = runtime.context
        from_open_id = ctx.open_id
        from_open_id_safe = sanitize_open_id(from_open_id)
        to_open_id_safe = sanitize_open_id(to_open_id)

        name_parts: list[str] = [purpose, "to", to_open_id_safe]
        if title.strip():
            name_parts.append(title.strip())
        name = " ".join(name_parts)

        content = "\n".join(
            [
                f"- purpose: {purpose}",
                f"- from_open_id: {from_open_id_safe}",
                f"- to_open_id: {to_open_id_safe}",
                "",
                "## Message",
                "",
                text.strip(),
                "",
            ]
        ).strip()

        path = write_knowledge_record(
            base_dir=base_dir,
            open_id=from_open_id,
            category="invites",
            name=name,
            kind="event",
            content=content,
            mode="replace",
        )
        root = knowledge_dir(base_dir=base_dir, open_id=from_open_id)
        rel_path = path.relative_to(root)
        logger.debug(
            "invite_send_mock success from_open_id={} to_open_id={} rel_path={} bytes={}",
            from_open_id_safe,
            to_open_id_safe,
            str(rel_path),
            path.stat().st_size,
        )
        return f"Invite logged to {rel_path} successfully"

    return [
        cast(BaseTool, knowledge_write),
        cast(BaseTool, knowledge_read),
        cast(BaseTool, knowledge_rename),
        cast(BaseTool, knowledge_tree),
        cast(BaseTool, invite_send_mock),
    ]
```

src/tools/knowledge_types.py
```
from typing import Literal

KnowledgeWriteMode = Literal["upsert", "replace"]
KnowledgeRecordKind = Literal["document", "event"]

```

src/types/context.py
```
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FeishuRuntimeContext:
    open_id: str
    history_to_load: int = 20

```

src/types/message.py
```
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
```

</source_code>