import os
def get_env(name: str, default="") -> str:
    value = os.environ.get(name)
    if not value and default == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value or default