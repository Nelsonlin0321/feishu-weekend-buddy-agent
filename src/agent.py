import os
from pydantic import SecretStr
from langchain_core.runnables import Runnable
from langchain.agents import create_agent

from src.model import build_model


DEEPINFRA_API_KEY =  SecretStr(os.getenv("DEEPINFRA_API_KEY",""))

def build_agent(
    system_prompt: str,
) -> Runnable:
    model = build_model()
    return create_agent(
        model=model,
        tools=[],
        system_prompt=system_prompt,
    )

if __name__ == "__main__":

    #  python -m src.agent
    from langchain_core.messages import HumanMessage
    start_messages = [HumanMessage(content="Hi")]
    agent = build_agent("You are a helpful assistant.")
    response = agent.invoke({"messages": start_messages})
    print(response)


