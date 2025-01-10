from django.db import models

from recipes.models import Recipe


class ShortLink(models.Model):
    short_code = models.CharField(max_length=10, unique=True)
    original_url = models.URLField()
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='short_links')

    def __str__(self):
        return f'{self.short_code} -> {self.original_url}'
