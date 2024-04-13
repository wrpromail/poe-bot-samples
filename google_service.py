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

# text to speech api service