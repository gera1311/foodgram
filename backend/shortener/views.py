import random
import string

from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect

from .models import ShortLink
from recipes.models import Recipe


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
        # Ищем короткую ссылку по short_code
        short_link = get_object_or_404(ShortLink, short_code=short_code)

        # Ищем рецепт по URL
        recipe_id = short_link.original_url.split('/')[-2]
        recipe = get_object_or_404(Recipe, id=recipe_id)

        # Перенаправляем на URL рецепта
        return redirect(f'/recipes/{recipe.id}/')
    except ShortLink.DoesNotExist:
        # Если короткая ссылка не найдена
        return HttpResponseNotFound('Короткая ссылка недействительна.')
