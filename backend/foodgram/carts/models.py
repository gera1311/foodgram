from django.db import models

from users.models import AbstractUser
from recipes.models import Recipe




class ShoppingCart(models.Model):
    pass
    
    class Meta:
        verbose_name = 'Продуктовая корзина'
        verbose_name_plural = 'Продуктовая корзина'
    
