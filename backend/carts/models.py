from django.db import models

from users.models import User
from recipes.models import Recipe


class ShoppingCart(models.Model):
    """Модель списка покупок."""
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='shopping_recipe',
        verbose_name='Рецепт'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_user',
        verbose_name='Пользователь'
    )

    class Meta:
        verbose_name = 'Продуктовая корзина'
        verbose_name_plural = 'Продуктовая корзина'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
