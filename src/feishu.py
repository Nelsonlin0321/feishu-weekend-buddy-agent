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
