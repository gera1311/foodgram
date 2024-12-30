from django.db import models
from django.contrib.auth.models import AbstractUser

from foodgram.settings import MAX_LENGTH_FOR_SHORT_VARIABLE


class User(AbstractUser):
    email = models.EmailField(
        max_length=MAX_LENGTH_FOR_SHORT_VARIABLE,
        unique=True,
    )
    avatar = models.ImageField(
        upload_to='users/', null=True, blank=True, verbose_name='Аватар'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        related_name='following',
        verbose_name='Пользователь (подписчик)',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name='follower',
        verbose_name='Пользователь (автор)',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_follow'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} -> {self.author}'
