import os
import dotenv
import json
from uuid import uuid4
import lark_oapi as lark
from lark_oapi.api.im.v1 import CreateMessageRequest,CreateMessageRequestBody,CreateMessageResponse

dotenv.load_dotenv()

FEISHU_APP_ID=os.getenv("FEISHU_APP_ID","")
FEISHU_APP_SECRET=os.getenv("FEISHU_APP_SECRET","")
if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
    raise ValueError("FEISHU_APP_ID and FEISHU_APP_SECRET are required")

def main():
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
    response: CreateMessageResponse = client.im.v1.message.create(request) # # pyright: ignore [reportOptionalMemberAccess]

    # 处理失败返回
    # if not response.success():
    #     lark.logger.error(
    #         f"client.im.v1.message.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
    #     return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))


if __name__ == "__main__":
    # python -m test.test_send_message
    main()