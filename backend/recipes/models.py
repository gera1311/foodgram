from django.db import models
from django.contrib.auth import get_user_model

from foodgram.settings import (
    MAX_LENGTH_FOR_SHORT_VARIABLE, MAX_LENGTH_FOR_DESCRIPTION)

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_FOR_SHORT_VARIABLE,
        verbose_name='Название')
    slug = models.SlugField(
        max_length=MAX_LENGTH_FOR_SHORT_VARIABLE,
        verbose_name='Slug')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_FOR_SHORT_VARIABLE,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_FOR_SHORT_VARIABLE,
        verbose_name='Единица измерения'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class Recipe(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_FOR_SHORT_VARIABLE,
        verbose_name='Название'
    )
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient',
        related_name='ingredient_recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='Теги')
    cooking_time = models.IntegerField(verbose_name='Время приготовления')
    text = models.CharField(max_length=MAX_LENGTH_FOR_DESCRIPTION,
                            verbose_name='Описание')
    image = models.ImageField(upload_to='recipes/images/',
                              verbose_name='Изображение')
    favorites = models.ManyToManyField(
        User,
        related_name='favorites_recipe',
        blank=True,
        verbose_name='Подписки'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author_recipes',
        blank=True,
        verbose_name='Автор'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} → {self.recipe}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe_ingredients',
                               verbose_name='Рецепт')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='recipe_ingredients',
                                   verbose_name='Ингредиент')
    amount = models.IntegerField(blank=True,
                                 null=True,
                                 verbose_name='Количество')

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipe_tags',
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецепта'
        ordering = ['recipe', 'tag__name']
