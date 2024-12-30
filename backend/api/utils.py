import base64
import uuid
import csv

from io import BytesIO
from django.http import HttpResponse
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas

from recipes.models import RecipeIngredient


def decode_base64_image(data, folder_name):
    try:
        format, imgstr = data.split(';base64,')
        ext = format.split('/')[-1]
        img_data = base64.b64decode(imgstr)

        file_name = f'{folder_name}/{uuid.uuid4()}.{ext}'
        return file_name, ContentFile(img_data)
    except (ValueError, IndexError, TypeError) as e:
        raise ValueError('Некорректный формат изображения') from e


def process_ingredients(recipe, ingredients_data):
    """
    Обрабатывает ингредиенты для рецепта:
    - Удаляет старые связи.
    - Создает новые записи через bulk_create.
    """
    RecipeIngredient.objects.filter(recipe=recipe).delete()

    recipe_ingredients = [
        RecipeIngredient(
            recipe=recipe,
            ingredient=ingredient_data['id'],
            amount=ingredient_data['amount']
        )
        for ingredient_data in ingredients_data
    ]

    RecipeIngredient.objects.bulk_create(recipe_ingredients)


class ShoppingCartFileGenerator:
    def generate_txt(self, ingredients):
        '''Генерация файла в формате TXT'''
        content = 'Список покупок:\n\n'
        for name, data in ingredients.items():
            content += f'- {name}: {data["amount"]} {data["unit"]}\n'
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; \
            filename="shopping_list.txt'
        return response

    def generate_pdf(self, ingredients):
        '''Генерация файла в формате PDF'''
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.drawString(100, 800, "Список покупок:")
        y = 750
        for name, data in ingredients.items():
            p.drawString(100, y, f"- {name}: {data['amount']} {data['unit']}")
            y -= 20
        p.showPage()
        p.save()
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; \
            filename="shopping_list.pdf"'
        return response

    def generate_csv(self, ingredients):
        '''Генерация файла в формате CSV'''
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; \
            filename="shopping_list.csv"'
        writer = csv.writer(response)
        writer.writerow(['Ингредиент', 'Количество', 'Единица измерения'])
        for name, data in ingredients.items():
            writer.writerow([name, data['amount'], data['unit']])
        return response
