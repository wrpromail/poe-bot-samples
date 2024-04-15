import requests
import io
import base64

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

def speech_to_text(source_type: int, source: str, target_language: str = 'zh-CN'):
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
        language_code=target_language) # speech API 不支持自动识别语言，自动识别语言需要 vertex AI API
    response = client.recognize(config=config, audio=audio)
    for result in response.results:
        pass # print(f'Transcript: {result.alternatives[0].transcript}')


# GCP speech to text api 响应速度偏慢，1分钟语音识别需要50+秒
def speech_to_text_by_http(source_type: int, source: str, api_key: str, target_language: str = 'zh-CN'):
    url = 'https://speech.googleapis.com/v1/speech:recognize?key=' + API_KEY
    if source_type == 0:
        with open(source, 'rb') as audio_file:
            audio_data = audio_file.read()

    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
    data = {
    "config": {
        "encoding": "LINEAR16",
        "sampleRateHertz": 16000,
        "languageCode": target_language
    },
    "audio": {
        "content": audio_b64
    }}
    response = requests.post(url, json=data)
    return response.json()



# text to speech api service