import dotenv
from src.utils import get_env
from pydantic import SecretStr
from langchain_deepseek import ChatDeepSeek
dotenv.load_dotenv()
DEEPINFRA_API_KEY = SecretStr(get_env("DEEPINFRA_API_KEY"))


def get_model(
    model_name: str="openai/gpt-oss-120b",
    reasoning: bool = True,
):
    llm = ChatDeepSeek(
        api_key=DEEPINFRA_API_KEY,
        api_base="https://api.deepinfra.com/v1/openai",
        model=model_name,
        extra_body={"reasoning": {"enabled": reasoning}},
    )
    return llm


if __name__ == "__main__":
    # python -m src.models
    model = get_model()
    print(model.invoke("Hello"))