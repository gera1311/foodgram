from django.db import models

from users.models import User
from recipes.models import Recipe


class ShoppingCart(models.Model):
    '''Модель списка покупок'''
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='shopping_carts'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_carts'
    )
    quantity = models.IntegerField

    class Meta:
        verbose_name = 'Продуктовая корзина'
        verbose_name_plural = 'Продуктовая корзина'
