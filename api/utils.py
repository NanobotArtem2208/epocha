from config.config import settings
import base64
import cv2
import numpy as np
import uuid

def correct_padding(data):
    missing_padding = len(data) % 4
    if missing_padding:
        data += "=" * (4 - missing_padding)
    return data


async def save_img(encoded_data, filename):
    encoded_data = correct_padding(encoded_data)
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return cv2.imwrite(filename, img)


# Генератор рандомного id
def random_id(num: int):
    return int(f"{num}{uuid.uuid4().int >> (128 - 32)}")


async def get_static_img_url(filename: str) -> str:
    return f"{settings.APP_URL}/{filename}"
