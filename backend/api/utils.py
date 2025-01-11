import base64
import uuid
import csv

from io import BytesIO
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.db.models import Sum
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.response import Response

from recipes.models import RecipeIngredient
from carts.models import ShoppingCart


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
    existing_ingredients = {
        ing.ingredient_id: ing for ing in RecipeIngredient.objects.filter(
            recipe=recipe)
    }

    new_ingredients = {item['id']: item['amount'] for item in ingredients_data}

    # Обновляем существующие ингредиенты или добавляем новые
    for ingredient_id, amount in new_ingredients.items():
        if ingredient_id in existing_ingredients:
            ingredient = existing_ingredients[ingredient_id]
            if ingredient.amount != amount:
                ingredient.amount = amount
                ingredient.save()
        else:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_id,
                amount=amount
            )

    # Удаляем ингредиенты, которые убраны из рецепта
    for ingredient_id in existing_ingredients.keys():
        if ingredient_id not in new_ingredients:
            existing_ingredients[ingredient_id].delete()


class ShoppingCartFileGenerator:
    def generate_txt(self, ingredients):
        """Генерация файла в формате TXT."""
        content = 'Список покупок:\n\n'
        for name, data in ingredients.items():
            content += f'- {name}: {data["amount"]} {data["unit"]}\n'
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; \
            filename="shopping_list.txt'
        return response

    def generate_pdf(self, ingredients):
        """Генерация файла в формате PDF."""
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
        """Генерация файла в формате CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; \
            filename="shopping_list.csv"'
        writer = csv.writer(response)
        writer.writerow(['Ингредиент', 'Количество', 'Единица измерения'])
        rows = [(name, data['amount'],
                 data['unit']) for name, data in ingredients.items()]
        writer.writerows(rows)
        return response


def generate_shopping_cart_report(user, file_format='txt'):
    shopping_cart = ShoppingCart.objects.filter(user=user)
    if not shopping_cart.exists():
        return None, 'Корзина покупок пуста.'

    # Подсчитываем ингредиенты
    ingredients = RecipeIngredient.objects.filter(
        recipe__shopping_recipe__user=user
    ).values(
        'ingredient__name',
        'ingredient__measurement_unit'
    ).annotate(
        total_amount=Sum('amount')
    )

    # Преобразуем в словарь для дальнейшего использования
    ingredients_dict = {
        ingredient['ingredient__name']: {
            'amount': ingredient['total_amount'],
            'unit': ingredient['ingredient__measurement_unit'],
        }
        for ingredient in ingredients
    }

    # Генерация файла
    file_generator = ShoppingCartFileGenerator()
    if file_format == 'txt':
        return file_generator.generate_txt(ingredients_dict), None
    elif file_format == 'pdf':
        return file_generator.generate_pdf(ingredients_dict), None
    elif file_format == 'csv':
        return file_generator.generate_csv(ingredients_dict), None
    else:
        return None, 'Укажите формат файла (txt, pdf, csv) в запросе.'


def handle_add_remove_action(model,
                             data,
                             error_message,
                             success_message):
    """Обрабатывает добавление или удаление объекта в модель Many-to-Many."""
    if model.objects.filter(**data).exists():
        return Response({'errors': error_message},
                        status=status.HTTP_400_BAD_REQUEST)

    model.objects.create(**data)
    return Response(success_message,
                    status=status.HTTP_201_CREATED)
