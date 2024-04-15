import requests
import io

from google.cloud import vision

# vision api service
def detech_image_annotations(vison_client, image_url):
    def check_image(image_content_bytes):
        try:
            image_content_bytes.verify()
            return True
        except:
            return False

    response = requests.get(image_url)
    if response.status_code != 200:
        return False, []
    image_bytes = io.BytesIO(response.content)
    if not check_image(image_bytes):
        return False, []
    image_bytes.seek(0)
    content = image_bytes.read()
    image = vision.Image(content=content)
    response = vison_client.text_detection(image=image)
    texts = response.text_annotations
    return True, texts

# speech to text api service
from google.cloud import speech_v1 as speech

def speech_to_text(source_type: int, source: str):
    client = speech.SpeechClient()
    # 0 本地文件
    if source_type == 0:
        with open(source, 'rb') as audio_file:
            content = audio_file.read()
    # 1 内存字节数据
    # 2 gcp cloud storage 云存储路径
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code='zh-CN') # speech API 不支持自动识别语言，自动识别语言需要 vertex AI API
    response = client.recognize(config=config, audio=audio)
    for result in response.results:
        pass # print(f'Transcript: {result.alternatives[0].transcript}')


# text to speech api service