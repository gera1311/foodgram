import random
import string

from django.http import HttpResponseRedirect, HttpResponseNotFound

from .models import ShortLink
from foodgram.settings import FRONTEND_URL


def generate_short_code(length=6):
    return ''.join(
        random.choices(string.ascii_letters + string.digits, k=length))


def create_short_link(original_url):
    short_code = generate_short_code()
    while ShortLink.objects.filter(short_code=short_code).exists():
        short_code = generate_short_code()

    short_link = ShortLink.objects.create(
        short_code=short_code, original_url=original_url)
    return short_link


def handle_short_link(request, short_code):
    try:
        # Ищем короткую ссылку в базе данных
        short_link = ShortLink.objects.get(short_code=short_code)
        recipe_id = short_link.recipe.id
        return HttpResponseRedirect(f'{FRONTEND_URL}/recipe/{recipe_id}')
    except ShortLink.DoesNotExist:
        # Если короткая ссылка не найдена
        return HttpResponseNotFound('Короткая ссылка недействительна.')
