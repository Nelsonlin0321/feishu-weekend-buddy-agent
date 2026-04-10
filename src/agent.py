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
    base_dir = Path(memory_base_dir)
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
