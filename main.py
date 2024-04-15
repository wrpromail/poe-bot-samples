from __future__ import annotations
from typing import AsyncIterable
import requests, time, random, string, os, json

import fastapi_poe as fp
import modal
from modal import asgi_app
from langdetect import detect
from modal import Image, Stub, Volume
from google.cloud import translate_v2 as translate
from google.oauth2.service_account import Credentials

from llm_service import normal_prompt_process
from llm_prompts import french_process_prompt

# 项目声明部分
# todo: 应用名称、依赖等内容需要改为配置化并进行版本管理
# 将需要的依赖在这里声明，modal 等 serverless 平台为你构建服务需要的运行环境镜像
REQUIREMENTS = ["fastapi-poe==0.0.36", "PyPDF2==3.0.1", "requests==2.31.0", "langdetect",
                "langchain-openai", "langchain","google-cloud-translate", "google-cloud-vision", "google-cloud-speech"]
image = Image.from_gcp_artifact_registry("us-west4-docker.pkg.dev/elite-destiny-420014/myreg/serverlessbase:testing",
                                         secret=modal.Secret.from_name("my-googlecloud-secret"), add_python="3.11").pip_install(*REQUIREMENTS)
#image = Image.debian_slim().pip_install(*REQUIREMENTS)
# 这里是对 app 的命名， modal 上的监控面板通过该名称区分不同的API服务
stub = Stub("filebot-poe2")
# 声明需要使用的 volume 名称
vol = Volume.from_name("my-volume")

# 常量管理
LANGDETECT_SUPPORT = ["en", "ja"]
# 机器人所使用的一些API服务密钥是通过 modal 平台管理的，而其环境变量是用户定义的
GOOGLE_SERVICE_ACCOUNT_JSON_ENV = "SERVICE_ACCOUNT_JSON"

# utils 
def generate_random_file_name():
    current_time = time.strftime("%Y%m%d")
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    file_name = f"{current_time}_{random_string}.txt"
    return file_name

# 文件输入处理逻辑
def process_plain_text_file(url: str):
    response = requests.get(url)
    if response.status_code != 200:
        return "read plain text file failed"
    # 模拟对文本的处理，这里可以是任何逻辑，如果是计算密集型，甚至可以考虑异步下发任务进行处理
    content = response.content.decode('utf-8')
    content = content.replace("", "")
    with open("/data/{}".format(generate_random_file_name()), "wb") as f:
        f.write(content.encode())
    return "read plain text file success: {}".format(content[:100])

def process_pdf_file(url: str):
    return "to be implemented"

# 调用 google translate 对于英文句子产生特定的处理
def sentence_translate_process(text: str, sa_json: str = GOOGLE_SERVICE_ACCOUNT_JSON_ENV):
    service_account_info = json.loads(os.environ[sa_json])
    credentials = Credentials.from_service_account_info(service_account_info)
    translate_client = translate.Client(credentials=credentials)
    translation = translate_client.translate(text, target_language="zh-CN")
    return translation["translatedText"]


class MyBot(fp.PoeBot):
    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        # request.query 是一个数组，允许获取用户输入的上下文
        last_query = request.query[-1]
        
        # 处理用户的附件输入
        if len(last_query.attachments) > 0:
            for attachment in last_query.attachments:
                if attachment.content_type == 'text/plain':
                    yield fp.PartialResponse(text=process_plain_text_file(attachment.url))
                    continue
                if attachment.content_type == 'application/pdf':
                    yield fp.PartialResponse(text=process_pdf_file(attachment.url))
                    continue
                else:
                    yield fp.PartialResponse(text=f"Attachment type: {attachment.content_type} is not supported right now")
        # 处理用户的文本输入
        last_message = last_query.content
        if last_message is None or last_message == "":
            yield fp.PartialResponse(text="\nNo message to process")
            return
        lang = detect(last_message)
        if lang == "fr":
            yield fp.PartialResponse(text=normal_prompt_process(last_message, french_process_prompt))
        if lang in LANGDETECT_SUPPORT:
            yield fp.PartialResponse(text=sentence_translate_process(last_message))
        else:
            yield fp.PartialResponse(text=last_message)
    
    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(allow_attachments=True)

# 全局注入业务需要使用的 secrets，这里 secret 的名称就是你在 modal 等 serverless 平台上注册的 secret 名称
@stub.function(secrets=[modal.Secret.from_name("my-googlecloud-secret"),modal.Secret.from_name("my-openai-secret")],
               image=image,volumes={"/data": vol})
@asgi_app()
def fastapi_app():
    bot = MyBot()
    # todo: allow_without_key should be set to False in production
    app = fp.make_app(bot, allow_without_key=True)
    return app