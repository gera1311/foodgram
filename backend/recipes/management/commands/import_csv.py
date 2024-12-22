import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient

TABLES = {
    Ingredient: 'ingredients.csv'
}


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with open(
            f'{settings.BASE_DIR}/data/ingredients.csv',
            'r',
            encoding='utf-8'
        ) as file:
            reader = csv.reader(file)
            objects = []
            for row in reader:
                name, measurement_unit = row
                obj = Ingredient(name=name, measurement_unit=measurement_unit)
                objects.append(obj)
            Ingredient.objects.bulk_create(objects, batch_size=500)
        self.stdout.write(self.style.SUCCESS('Данные загружены'))
