from __future__ import annotations
from typing import AsyncIterable
import requests, time, random, string, os, json

import fastapi_poe as fp
import modal
from modal import asgi_app
from langdetect import detect
from modal import Image, Stub, Volume
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from google.cloud import translate_v2 as translate
from google.oauth2.service_account import Credentials


# todo: 应用名称、依赖等内容需要改为配置化并进行版本管理
REQUIREMENTS = ["fastapi-poe==0.0.36", "PyPDF2==3.0.1", "requests==2.31.0", "langdetect",
                "langchain-openai", "langchain","google-cloud-translate"]
image = Image.debian_slim().pip_install(*REQUIREMENTS)
stub = Stub("filebot-poe2")
vol = Volume.from_name("my-volume")


def generate_random_file_name():
    current_time = time.strftime("%Y%m%d")
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    file_name = f"{current_time}_{random_string}.txt"
    return file_name

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


french_process_prompt = """
请使用中文逐字逐词给我讲解下面的法语内容，如果有重要的语法点或惯用语也请说明，最后仿造两个类似的法语句子。{french_sentence}"""

def french_sentence_process(raw: str):
    llm = ChatOpenAI(temperature=0.2)
    prompt = ChatPromptTemplate.from_messages([
        ("system","You are french language teacher."),
        ("user", "{input}")
    ])
    chain = prompt | llm
    response = chain.invoke({"input":french_process_prompt.format(french_sentence=raw)})
    return response.content

def sentence_translate_process(raw: str):
    service_account_info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
    credentials = Credentials.from_service_account_info(service_account_info)
    translate_client = translate.Client(credentials=credentials)
    translation = translate_client.translate(raw, target_language="zh-CN")
    return translation["translatedText"]
    
class MyBot(fp.PoeBot):
    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        last_query = request.query[-1]
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
            
        last_message = last_query.content
        if last_message is None or last_message == "":
            yield fp.PartialResponse(text="\nNo message to process")
            return
        lang = detect(last_message)
        if lang == "fr":
            yield fp.PartialResponse(text=french_sentence_process(last_message))
        if lang in ["en"]:
            yield fp.PartialResponse(text=sentence_translate_process(last_message))
        else:
            yield fp.PartialResponse(text=last_message)
    
    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(allow_attachments=True)


@stub.function(secrets=[modal.Secret.from_name("my-googlecloud-secret"),modal.Secret.from_name("my-openai-secret")],
               image=image,volumes={"/data": vol})
@asgi_app()
def fastapi_app():
    bot = MyBot()
    # todo: allow_without_key should be set to False in production
    app = fp.make_app(bot, allow_without_key=True)
    return app