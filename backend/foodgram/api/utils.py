import base64
import uuid

from django.core.files.base import ContentFile


def decode_base64_image(data, folder_name='avatars'):
    try:
        format, imgstr = data.split(';base64,')
        ext = format.split('/')[-1]
        img_data = base64.b64decode(imgstr)

        file_name = f'{folder_name}/{uuid.uuid4()}.{ext}'
        return file_name, ContentFile(img_data)
    except (ValueError, IndexError, TypeError) as e:
        raise ValueError('Некорректный формат изображения') from e
