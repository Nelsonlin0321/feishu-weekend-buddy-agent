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